"""
services/runner.py
──────────────────
Spawns piemr_assignment_upload.py as a subprocess.
Uses a background thread and standard subprocess.Popen for maximum 
compatibility with Windows/Uvicorn event loop restrictions.
"""

import asyncio
import json
import os
import tempfile
import sys
import subprocess
import logging
from typing import Optional

log = logging.getLogger(__name__)

# run_id  →  asyncio.Queue  (None sentinel = stream finished)
active_runs: dict[int, asyncio.Queue] = {}

# run_id  →  subprocess.Popen (tracks actual process objects to allow termination)
running_processes: dict[int, subprocess.Popen] = {}


async def start_run(
    user_id: int,
    username: str,
    password: str,
    file_path: str,
    triggered_by: str = "manual",
    file_id: Optional[int] = None,
) -> int:
    """Create a DB record, spin up the background task, return run_id."""
    import db
    run_id = await db.create_run(user_id=user_id, triggered_by=triggered_by, file_id=file_id)
    queue: asyncio.Queue = asyncio.Queue()
    active_runs[run_id] = queue

    # Run the executor in a separate thread to avoid blocking the async loop
    # and to bypass asyncio.create_subprocess_exec restrictions on Windows.
    asyncio.create_task(
        _execute(run_id, username, password, file_path, queue)
    )
    return run_id


def _sync_subprocess_worker(run_id, cmd, queue, loop):
    """
    Synchronous worker running in a thread. 
    Reads stdout line by line and pushes to the async queue.
    """
    full_log = []
    uploads_total = 0
    status = "error"
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='replace'
        )
        
        # Register the process so it can be killed later
        running_processes[run_id] = process

        for line in iter(process.stdout.readline, ""):
            line = line.rstrip()
            full_log.append(line)
            # Safely put into the async queue from this thread
            loop.call_soon_threadsafe(queue.put_nowait, line)
            
            if "Total uploads:" in line:
                try:
                    uploads_total = int(line.split("Total uploads:")[-1].strip())
                except:
                    pass

        process.wait()
        
        if process.returncode == 0:
            status = "success"
        elif process.returncode in [-15, 15, 1, 3221225786]: # Common termination codes (SIGTERM, Windows exit)
            # If it was in running_processes, and it's gone, it might have been stopped
            # but we can't be 100% sure here without more state. 
            # However, if it produced the "COMPLETE" line, it's a success.
            is_complete = any("COMPLETE" in l for l in full_log[-5:])
            status = "success" if is_complete else "stopped"
        else:
            status = "error"
            
    except Exception as e:
        err = f"THREAD RUNNER ERROR: {e}"
        full_log.append(err)
        loop.call_soon_threadsafe(queue.put_nowait, err)
        status = "error"
    finally:
        # Unregister process
        running_processes.pop(run_id, None)
        
    return status, uploads_total, "\n".join(full_log)


async def _execute(
    run_id: int,
    username: str,
    password: str,
    file_path: str,
    queue: asyncio.Queue,
):
    """Background entry point: handles temp file and thread coordination."""
    import db
    loop = asyncio.get_running_loop()
    tmp_path = None
    
    try:
        # 1. Prepare temp config
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".json", prefix="piemr_")
        from config import settings
        cfg_data = {
            "username": username,
            "password": password,
            "file": os.path.abspath(file_path),
            "headless": settings.headless,
        }
        if settings.chromedriver_path:
            cfg_data["chromedriver_path"] = settings.chromedriver_path

        with os.fdopen(tmp_fd, "w") as f:
            json.dump(cfg_data, f)

        # 2. Prepare command
        from config import settings
        cmd = [
            sys.executable,
            os.path.abspath(settings.script_path),
            "--config", tmp_path
        ]
        
        log.info(f"Starting threaded runner for run_id={run_id}")
        
        # 3. Offload to thread
        status, uploads, logs = await asyncio.to_thread(_sync_subprocess_worker, run_id, cmd, queue, loop)

    except Exception as exc:
        err = f"RUNNER WRAPPER ERROR: {exc}"
        log.error(err)
        await queue.put(err)
        status = "error"
        uploads = 0
        logs = err

    finally:
        # 4. Clean up
        if tmp_path and os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except: pass
            
        # 5. Save to DB
        await db.finish_run(run_id, status, uploads, logs)
        active_runs.pop(run_id, None)

        # 6. Signal end to stream
        await queue.put(None)


async def stream_run(run_id: int):
    """SSE log streamer."""
    import db
    if run_id in active_runs:
        queue = active_runs[run_id]
        while True:
            try:
                line = await asyncio.wait_for(queue.get(), timeout=120)
            except asyncio.TimeoutError:
                yield "[stream timeout]"
                break
            if line is None:
                break
            yield line
    else:
        run = await db.get_run(run_id)
        if run and run.get("log_text"):
            for line in run["log_text"].split("\n"):
                yield line


async def stop_run(run_id: int):
    """Kills the subprocess associated with run_id."""
    process = running_processes.get(run_id)
    if process:
        log.info(f"Terminating run_id={run_id}")
        process.terminate()
        # The _sync_subprocess_worker thread will naturally exit, cleanup 
        # is handled in finally blocks there and in _execute.
        return True
    return False
