"""
services/scheduler.py
─────────────────────
APScheduler wrapper.  One job: fire the upload script daily at user-set time.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import db

log = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def setup(app=None):
    """Called from FastAPI lifespan. Loads all saved schedules from DB."""
    scheduler.start()
    async with db.pool().acquire() as conn:
        rows = await conn.fetch("SELECT user_id, schedule_time FROM config WHERE schedule_enabled = TRUE")
        for r in rows:
            _add_job(r["user_id"], r["schedule_time"])
            log.info("Scheduler: Loaded job for user_id=%d — daily at %s", r["user_id"], r["schedule_time"])


async def enable(user_id: int, time_str: str):
    """Enable (or reschedule) the daily job for a specific user."""
    from config import settings
    await db.update_schedule(user_id, time_str, enabled=True)
    _remove_job(user_id)
    _add_job(user_id, time_str)
    log.info("Scheduler: Enabled job for user_id=%d — daily at %s (%s)", user_id, time_str, settings.scheduler_timezone)


async def disable(user_id: int):
    """Pause the daily job for a specific user."""
    cfg = await db.get_config(user_id)
    await db.update_schedule(user_id, cfg.get("schedule_time", "08:00"), enabled=False)
    _remove_job(user_id)
    log.info("Scheduler: Disabled job for user_id=%d.", user_id)


def next_run_time(user_id: int) -> str | None:
    job = scheduler.get_job(_job_id(user_id))
    if job and job.next_run_time:
        return job.next_run_time.isoformat()
    return None


async def trigger_user_job(user_id: int):
    """Manually fire the background job for one user immediately."""
    import asyncio
    asyncio.create_task(_daily_job(user_id))


# ── Internal ─────────────────────────────────────────────────────────────────

def _job_id(user_id: int) -> str:
    return f"daily_upload_{user_id}"


def _add_job(user_id: int, time_str: str):
    from config import settings
    hour, minute = map(int, time_str.split(":"))
    scheduler.add_job(
        _daily_job,
        args=[user_id],
        trigger=CronTrigger(hour=hour, minute=minute, timezone=settings.scheduler_timezone),
        id=_job_id(user_id),
        replace_existing=True,
        misfire_grace_time=60,
    )


def _remove_job(user_id: int):
    try:
        scheduler.remove_job(_job_id(user_id))
    except Exception:
        pass


async def _daily_job(user_id: int):
    """Fired by APScheduler. Loads config from DB for the specific user."""
    from services.runner import start_run

    log.info("Scheduler: Firing job for user_id=%d...", user_id)
    cfg = await db.get_config(user_id)

    if not cfg.get("username") or not cfg.get("password") or not cfg.get("file_id"):
        log.warning("Scheduler: User_id=%d config incomplete, skipping run.", user_id)
        return

    # Verify file still exists on disk before starting
    file_record = await db.get_file(cfg["file_id"])
    if not file_record:
        log.warning("Scheduler: User_id=%d saved file record not found, skipping run.", user_id)
        return

    import os
    if not os.path.exists(file_record["file_path"]):
        log.warning("Scheduler: File no longer on disk for user_id=%d, skipping run.", user_id)
        return

    try:
        run_id = await start_run(
            user_id=user_id,
            username=cfg["username"],
            password=cfg["password"],
            file_path=file_record["file_path"],
            triggered_by="scheduler",
            file_id=cfg["file_id"],
        )
        log.info("Scheduler: User_id=%d run_id=%d started.", user_id, run_id)
    except Exception as e:
        log.error("Scheduler: User_id=%d failed to start — %s", user_id, e)
