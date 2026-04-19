"""
main.py
───────
FastAPI application entry point.
Registers all routers, initialises DB and scheduler on startup.
"""

import logging
from contextlib import asynccontextmanager

import os
import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import settings
import db
from services.scheduler import setup as scheduler_setup
from routers.run import router as run_router
from routers.config import router as config_router
from routers.schedule import router as schedule_router
from routers.auth import router as auth_router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s  —  %(message)s",
)
log = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting up...")
    await db.init_db()
    await scheduler_setup()
    log.info("Ready.")
    yield
    log.info("Shutting down...")
    from services.scheduler import scheduler
    scheduler.shutdown(wait=False)
    await db.close_db()


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="PIEMR Auto-Uploader API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routes ────────────────────────────────────────────────────────────────

app.include_router(auth_router,     prefix="/api")
app.include_router(run_router,      prefix="/api")
app.include_router(config_router,   prefix="/api")
app.include_router(schedule_router, prefix="/api")


# ── Serve built React frontend (optional — skip if using separate dev server) ─

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Catch-all: return index.html so React Router handles routing."""
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# ── Dev entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        loop="asyncio", # Force standard asyncio loop on Windows
        workers=1,     # Must be 1 — scheduler and run queue are in-process
    )
