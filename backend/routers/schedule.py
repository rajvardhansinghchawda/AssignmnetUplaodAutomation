"""
routers/schedule.py
───────────────────
GET  /api/schedule         — current schedule info + next run time
POST /api/schedule/enable  — enable and set time
POST /api/schedule/disable — disable
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from routers.auth import get_current_user
import db
from services.scheduler import enable, disable, next_run_time, trigger_user_job

router = APIRouter()


class EnableBody(BaseModel):
    time: str   # "HH:MM"


@router.get("/schedule")
async def get_schedule(current_user: dict = Depends(get_current_user)):
    cfg = await db.get_config(current_user["id"])
    return {
        "schedule_time": cfg.get("schedule_time", "08:00"),
        "schedule_enabled": bool(cfg.get("schedule_enabled", 0)),
        "next_run_time": next_run_time(current_user["id"]),
    }


@router.post("/schedule/enable")
async def enable_schedule(body: EnableBody, current_user: dict = Depends(get_current_user)):
    await enable(current_user["id"], body.time)
    return {
        "enabled": True,
        "schedule_time": body.time,
        "next_run_time": next_run_time(current_user["id"]),
    }


@router.post("/schedule/disable")
async def disable_schedule(current_user: dict = Depends(get_current_user)):
    await disable(current_user["id"])
    return {"enabled": False}


@router.post("/schedule/test")
async def test_schedule(current_user: dict = Depends(get_current_user)):
    """Manually trigger the daily job for the current user right now for testing."""
    await trigger_user_job(current_user["id"])
    return {"triggered": True, "message": "Scheduler task started for your account."}
