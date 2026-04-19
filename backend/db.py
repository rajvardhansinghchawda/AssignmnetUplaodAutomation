"""
db.py — PostgreSQL backend via asyncpg
───────────────────────────────────────
Tables
  runs    — every script execution (manual or scheduled)
  config  — single-row: portal credentials + schedule settings
  files   — every uploaded assignment file (for re-use across runs)
"""

import asyncpg
from datetime import datetime, timezone
from typing import Optional

from config import settings

# Module-level connection pool (initialised in init_db)
_pool: Optional[asyncpg.Pool] = None


# ── Pool lifecycle ────────────────────────────────────────────────────────────

async def init_db():
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=2,
        max_size=10,
        command_timeout=30,
    )
    async with _pool.acquire() as conn:
        await _create_tables(conn)


async def close_db():
    if _pool:
        await _pool.close()


def pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialised. Call init_db() first.")
    return _pool


# ── Schema ────────────────────────────────────────────────────────────────────

async def _create_tables(conn: asyncpg.Connection):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              SERIAL PRIMARY KEY,
            email           TEXT        NOT NULL UNIQUE,
            full_name       TEXT,
            picture         TEXT,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS files (
            id              SERIAL PRIMARY KEY,
            user_id         INTEGER     REFERENCES users(id),
            original_name   TEXT        NOT NULL,
            stored_name     TEXT        NOT NULL,
            file_path       TEXT        NOT NULL UNIQUE,
            file_size       BIGINT      NOT NULL DEFAULT 0,
            uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            use_count       INTEGER     NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS runs (
            id              SERIAL PRIMARY KEY,
            user_id         INTEGER     REFERENCES users(id),
            started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            finished_at     TIMESTAMPTZ,
            triggered_by    TEXT        NOT NULL DEFAULT 'manual',
            status          TEXT        NOT NULL DEFAULT 'running',
            uploads_total   INTEGER     NOT NULL DEFAULT 0,
            log_text        TEXT        NOT NULL DEFAULT '',
            file_id         INTEGER     REFERENCES files(id)
        );

        CREATE TABLE IF NOT EXISTS config (
            user_id           INTEGER     PRIMARY KEY REFERENCES users(id),
            username          TEXT        NOT NULL DEFAULT '',
            password          TEXT        NOT NULL DEFAULT '',
            file_id           INTEGER     REFERENCES files(id),
            schedule_time     TEXT        NOT NULL DEFAULT '08:00',
            schedule_enabled  BOOLEAN     NOT NULL DEFAULT FALSE,
            updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)

    # Migrations for existing tables
    await conn.execute("""
        DO $$
        BEGIN
            -- Add new columns if they don't exist
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='full_name') THEN
                ALTER TABLE users ADD COLUMN full_name TEXT;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='picture') THEN
                ALTER TABLE users ADD COLUMN picture TEXT;
            END IF;
            -- Drop hashed_password if it exists
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='hashed_password') THEN
                ALTER TABLE users DROP COLUMN hashed_password;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='files' AND column_name='user_id') THEN
                ALTER TABLE files ADD COLUMN user_id INTEGER REFERENCES users(id);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='runs' AND column_name='user_id') THEN
                ALTER TABLE runs ADD COLUMN user_id INTEGER REFERENCES users(id);
            END IF;

            -- Fix 'config' table if it uses old single-user schema (PK 'id' instead of 'user_id')
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='config') THEN
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='config' AND column_name='id') AND 
                   NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='config' AND column_name='user_id') THEN
                    DROP TABLE config CASCADE;
                END IF;
            END IF;
        END $$;
    """)

# ── Users ─────────────────────────────────────────────────────────────────────

async def create_user(email: str, full_name: str, picture: str) -> int:
    async with pool().acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO users (email, full_name, picture)
            VALUES ($1, $2, $3)
            RETURNING id
        """, email, full_name, picture)
        return row["id"]


async def get_user_by_email(email: str) -> Optional[dict]:
    async with pool().acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
        return dict(row) if row else None


async def get_user_by_id(user_id: int) -> Optional[dict]:
    async with pool().acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return dict(row) if row else None


# ── Files ─────────────────────────────────────────────────────────────────────

async def save_file(
    user_id: int,
    original_name: str,
    stored_name: str,
    file_path: str,
    file_size: int,
) -> int:
    """
    Insert a new file record.  If a file with the same path already exists
    (same filename re-uploaded), update it and return the same id.
    """
    async with pool().acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO files (user_id, original_name, stored_name, file_path, file_size)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (file_path) DO UPDATE
                SET original_name = EXCLUDED.original_name,
                    stored_name   = EXCLUDED.stored_name,
                    file_size     = EXCLUDED.file_size,
                    uploaded_at   = NOW()
            RETURNING id
        """, user_id, original_name, stored_name, file_path, file_size)
        return row["id"]


async def get_file(file_id: int) -> Optional[dict]:
    async with pool().acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM files WHERE id = $1", file_id)
        return dict(row) if row else None


async def list_files(user_id: int) -> list:
    """Return all uploaded files for a user, most recently used first."""
    async with pool().acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, original_name, stored_name, file_path,
                   file_size, uploaded_at, use_count
            FROM files
            WHERE user_id = $1
            ORDER BY uploaded_at DESC
        """, user_id)
        return [dict(r) for r in rows]


async def increment_file_use(file_id: int):
    async with pool().acquire() as conn:
        await conn.execute(
            "UPDATE files SET use_count = use_count + 1 WHERE id = $1", file_id
        )


async def delete_file_record(file_id: int):
    """Remove DB record only — caller deletes the file on disk."""
    async with pool().acquire() as conn:
        await conn.execute("DELETE FROM files WHERE id = $1", file_id)


# ── Runs ──────────────────────────────────────────────────────────────────────

async def create_run(user_id: int, triggered_by: str = "manual", file_id: Optional[int] = None) -> int:
    async with pool().acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO runs (user_id, triggered_by, file_id)
            VALUES ($1, $2, $3)
            RETURNING id
        """, user_id, triggered_by, file_id)
        return row["id"]


async def finish_run(run_id: int, status: str, uploads_total: int, log_text: str):
    async with pool().acquire() as conn:
        await conn.execute("""
            UPDATE runs
            SET finished_at   = NOW(),
                status        = $1,
                uploads_total = $2,
                log_text      = $3
            WHERE id = $4
        """, status, uploads_total, log_text, run_id)


async def get_run(run_id: int) -> Optional[dict]:
    async with pool().acquire() as conn:
        row = await conn.fetchrow("""
            SELECT r.*, f.original_name AS file_name
            FROM runs r
            LEFT JOIN files f ON f.id = r.file_id
            WHERE r.id = $1
        """, run_id)
        return dict(row) if row else None


async def get_runs(user_id: int, limit: int = 20) -> list:
    async with pool().acquire() as conn:
        rows = await conn.fetch("""
            SELECT r.id, r.started_at, r.finished_at, r.triggered_by,
                   r.status, r.uploads_total, r.file_id,
                   f.original_name AS file_name
            FROM runs r
            LEFT JOIN files f ON f.id = r.file_id
            WHERE r.user_id = $1
            ORDER BY r.started_at DESC
            LIMIT $2
        """, user_id, limit)
        return [dict(r) for r in rows]


async def get_last_run(user_id: int) -> Optional[dict]:
    runs = await get_runs(user_id, limit=1)
    return runs[0] if runs else None


# ── Config ────────────────────────────────────────────────────────────────────

async def save_config(
    user_id: int,
    username: str,
    password: str,
    file_id: int,
    schedule_time: str,
    schedule_enabled: bool,
):
    async with pool().acquire() as conn:
        await conn.execute("""
            INSERT INTO config (user_id, username, password, file_id, schedule_time, schedule_enabled, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
            ON CONFLICT (user_id) DO UPDATE
            SET username         = EXCLUDED.username,
                password         = EXCLUDED.password,
                file_id          = EXCLUDED.file_id,
                schedule_time    = EXCLUDED.schedule_time,
                schedule_enabled = EXCLUDED.schedule_enabled,
                updated_at       = NOW()
        """, user_id, username, password, file_id, schedule_time, schedule_enabled)


async def get_config(user_id: int) -> dict:
    async with pool().acquire() as conn:
        row = await conn.fetchrow("""
            SELECT c.*, f.file_path, f.original_name AS file_name
            FROM config c
            LEFT JOIN files f ON f.id = c.file_id
            WHERE c.user_id = $1
        """, user_id)
        return dict(row) if row else {}


async def update_schedule(user_id: int, schedule_time: str, enabled: bool):
    async with pool().acquire() as conn:
        await conn.execute("""
            UPDATE config
            SET schedule_time    = $1,
                schedule_enabled = $2,
                updated_at       = NOW()
            WHERE user_id = $3
        """, schedule_time, enabled, user_id)
