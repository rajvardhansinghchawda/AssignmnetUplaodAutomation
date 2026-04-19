"""
routers/run.py
──────────────
POST /api/run           — start a run
                          multipart fields: username, password
                          + EITHER:  file (new upload)
                          + OR:      file_id (integer, use past file)
GET  /api/run/stream    — SSE live log stream (?run_id=N)
GET  /api/runs          — run history
GET  /api/runs/{run_id} — single run detail with full log
GET  /api/status/last   — most recent run summary
"""

import os
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

import db
from config import settings
from routers.auth import get_current_user
from services.runner import active_runs, start_run, stream_run, stop_run

router = APIRouter()
UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ── POST /api/run ─────────────────────────────────────────────────────────────

@router.post("/run")
async def trigger_run(
    username: str = Form(...),
    password: str = Form(None),
    # Option A: pick an already-stored file by its DB id
    file_id: str = Form(None),
    # Option B: upload a new file right now
    file: UploadFile = File(None),
    current_user: dict = Depends(get_current_user),
):
    # Guard: only one concurrent run
    if active_runs:
        raise HTTPException(409, "A run is already in progress.")

    resolved_file_id: int | None = None
    file_path: str = ""
    existing_cfg = await db.get_config(current_user["id"])

    # ── Handle Password Fallback ────────────────────────────────────────────
    final_password = password
    if not final_password or not final_password.strip():
        final_password = existing_cfg.get("password")
    
    if not final_password:
        raise HTTPException(400, "Password is required (none found in saved config).")

    if file_id and file_id.strip():
        # ── Use a past file ──────────────────────────────────────────────────
        fid = int(file_id)
        record = await db.get_file(fid)
        if not record:
            raise HTTPException(404, f"File id={fid} not found.")
        if not os.path.exists(record["file_path"]):
            raise HTTPException(410, f"File '{record['original_name']}' no longer exists on disk.")
        file_path = record["file_path"]
        resolved_file_id = fid

    elif file and file.filename:
        # ── New file upload ───────────────────────────────────────────────────
        contents = await file.read()
        if len(contents) > settings.max_upload_bytes:
            raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit.")

        dest = UPLOAD_DIR / file.filename
        dest.write_bytes(contents)
        file_path = str(dest)

        resolved_file_id = await db.save_file(
            user_id=current_user["id"],
            original_name=file.filename,
            stored_name=file.filename,
            file_path=file_path,
            file_size=len(contents),
        )
    else:
        # ── Fallback to last file in config ───────────────────────────────────
        resolved_file_id = existing_cfg.get("file_id")
        if not resolved_file_id:
            raise HTTPException(400, "No file provided and no past file found.")
        
        record = await db.get_file(resolved_file_id)
        if not record or not os.path.exists(record["file_path"]):
            raise HTTPException(410, "Saved file no longer exists.")
        file_path = record["file_path"]

    # Track usage count
    await db.increment_file_use(resolved_file_id)

    # Start subprocess (non-blocking)
    run_id = await start_run(
        user_id=current_user["id"],
        username=username,
        password=final_password,
        file_path=file_path,
        triggered_by="manual",
        file_id=resolved_file_id,
    )

    file_record = await db.get_file(resolved_file_id)
    return {
        "run_id": run_id,
        "file_id": resolved_file_id,
        "file_name": file_record["original_name"] if file_record else None,
    }


# ── GET /api/run/stream ───────────────────────────────────────────────────────

@router.get("/run/stream")
async def run_stream(run_id: int, current_user: dict = Depends(get_current_user)):
    """Server-Sent Events — browser opens EventSource on this URL."""
    # Verify owner
    run = await db.get_run(run_id)
    if not run or run["user_id"] != current_user["id"]:
        raise HTTPException(403, "Forbidden")

    async def generator():
        async for line in stream_run(run_id):
            yield f"data: {line}\n\n"
        yield "event: done\ndata: complete\n\n"

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── GET /api/run/active ───────────────────────────────────────────────────────

@router.get("/run/active")
async def active_run_info(current_user: dict = Depends(get_current_user)):
    """Returns the ID of the currently running logic for this user."""
    run = await db.get_active_run(current_user["id"])
    return run


# ── POST /api/run/{run_id}/stop ───────────────────────────────────────────────

@router.post("/run/{run_id}/stop")
async def abort_run(run_id: int, current_user: dict = Depends(get_current_user)):
    """Kills an active run."""
    run = await db.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found.")
    if run["user_id"] != current_user["id"]:
        raise HTTPException(403, "Forbidden")
    
    success = await stop_run(run_id)
    if not success:
        raise HTTPException(400, "Run is not active or already finished.")
    
    return {"status": "stopping", "run_id": run_id}


# ── GET /api/runs ─────────────────────────────────────────────────────────────

@router.get("/runs")
async def list_runs(current_user: dict = Depends(get_current_user), limit: int = 20):
    runs = await db.get_runs(current_user["id"], limit=min(limit, 100))
    # Add convenience fields for the frontend
    local_tz = ZoneInfo(settings.scheduler_timezone)
    for r in runs:
        if r["started_at"]:
            local_dt = r["started_at"].astimezone(local_tz)
            r["timestamp"] = local_dt.isoformat()
            r["formatted_date"] = local_dt.strftime("%d %b, %H:%M")
        r["upload_count"] = r.get("uploads_total", 0)
        r.pop("log_text", None)
    return runs


# ── GET /api/runs/{run_id} ────────────────────────────────────────────────────

@router.get("/runs/{run_id}")
async def get_run_detail(run_id: int, current_user: dict = Depends(get_current_user)):
    run = await db.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found.")
    if run["user_id"] != current_user["id"]:
        raise HTTPException(403, "Forbidden")
    return run


# ── GET /api/status/last ──────────────────────────────────────────────────────

@router.get("/status/last")
async def last_status(current_user: dict = Depends(get_current_user)):
    run = await db.get_last_run(current_user["id"])
    if not run:
        return {"status": "never_run"}
    
    # Map fields for frontend convenience
    local_tz = ZoneInfo(settings.scheduler_timezone)
    if run.get("started_at"):
        local_dt = run["started_at"].astimezone(local_tz)
        run["timestamp"] = local_dt.isoformat()
        run["formatted_date"] = local_dt.strftime("%d %b, %H:%M")
    
    run["upload_count"] = run.get("uploads_total", 0)
    run.pop("log_text", None)
    return run
