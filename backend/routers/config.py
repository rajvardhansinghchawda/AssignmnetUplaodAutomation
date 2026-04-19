"""
routers/config_router.py
────────────────────────
POST /api/config            — save credentials + schedule  (new file OR existing file_id)
GET  /api/config            — load saved config (no password)
GET  /api/files             — list all previously uploaded files
DELETE /api/files/{file_id} — remove a past file from DB + disk
"""

import os
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from routers.auth import get_current_user

import db
from config import settings

router = APIRouter()
UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ── POST /api/config ──────────────────────────────────────────────────────────

@router.post("/config")
async def save_config(
    username: str = Form(...),
    password: str = Form(...),
    schedule_time: str = Form("08:00"),
    schedule_enabled: str = Form("false"),
    # User picks a past file by its DB id (no new upload)
    file_id: str = Form(None),
    # Or uploads a brand-new file
    file: UploadFile = File(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Two modes:
      • file_id is set   → use an already-stored file (no upload needed)
      • file is provided → save new file to disk + DB, get its id
    """
    resolved_file_id: int | None = None

    if file_id and file_id.strip():
        # ── Mode A: user selected a past upload ─────────────────────────────
        fid = int(file_id)
        record = await db.get_file(fid)
        if not record:
            raise HTTPException(404, f"File id={fid} not found.")
        if not os.path.exists(record["file_path"]):
            raise HTTPException(410, f"File '{record['original_name']}' no longer exists on disk.")
        resolved_file_id = fid

    elif file and file.filename:
        # ── Mode B: new file uploaded ────────────────────────────────────────
        contents = await file.read()
        if len(contents) > settings.max_upload_bytes:
            raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit.")

        # Use a safe stored name to avoid collisions  (keep original for display)
        stored_name = file.filename
        dest = UPLOAD_DIR / stored_name
        dest.write_bytes(contents)

        resolved_file_id = await db.save_file(
            user_id=current_user["id"],
            original_name=file.filename,
            stored_name=stored_name,
            file_path=str(dest),
            file_size=len(contents),
        )
    else:
        # No new file — fall back to whatever is already in config
        current = await db.get_config(current_user["id"])
        resolved_file_id = current.get("file_id")
        if not resolved_file_id:
            raise HTTPException(400, "No file provided and no previous file found.")

    enabled = schedule_enabled.lower() in ("true", "1", "yes")

    await db.save_config(
        user_id=current_user["id"],
        username=username,
        password=password,
        file_id=resolved_file_id,
        schedule_time=schedule_time,
        schedule_enabled=enabled,
    )

    from services.scheduler import enable as sched_enable, disable as sched_disable
    if enabled:
        await sched_enable(current_user["id"], schedule_time)
    else:
        await sched_disable(current_user["id"])

    file_record = await db.get_file(resolved_file_id)
    return {
        "saved": True,
        "file_id": resolved_file_id,
        "file_name": file_record["original_name"] if file_record else None,
        "schedule_time": schedule_time,
        "schedule_enabled": enabled,
    }


# ── GET /api/config ───────────────────────────────────────────────────────────

@router.get("/config")
async def get_config(current_user: dict = Depends(get_current_user)):
    cfg = await db.get_config(current_user["id"])
    return {
        "username": cfg.get("username", ""),
        "file_id": cfg.get("file_id"),
        "file_name": cfg.get("file_name"),
        "schedule_time": cfg.get("schedule_time", "08:00"),
        "schedule_enabled": bool(cfg.get("schedule_enabled", False)),
        "updated_at": cfg.get("updated_at"),
        # password deliberately excluded
    }


# ── GET /api/files ────────────────────────────────────────────────────────────

@router.get("/files")
async def list_files(current_user: dict = Depends(get_current_user)):
    """
    Returns all previously uploaded files so the frontend can show
    a 'Select past upload' picker.
    """
    files = await db.list_files(current_user["id"])
    # Annotate with whether the file still exists on disk
    for f in files:
        f["exists_on_disk"] = os.path.exists(f["file_path"])
        f["file_size_kb"] = round(f["file_size"] / 1024, 1)
    return files


# ── DELETE /api/files/{file_id} ───────────────────────────────────────────────

@router.delete("/files/{file_id}")
async def delete_file(file_id: int, current_user: dict = Depends(get_current_user)):
    """Remove a past file from the DB and from disk."""
    record = await db.get_file(file_id)
    if not record:
        raise HTTPException(404, "File not found.")
    
    if record["user_id"] != current_user["id"]:
        raise HTTPException(403, "Forbidden")

    # Remove from disk (best-effort)
    try:
        os.remove(record["file_path"])
    except FileNotFoundError:
        pass

    await db.delete_file_record(file_id)
    return {"deleted": True, "file_name": record["original_name"]}
