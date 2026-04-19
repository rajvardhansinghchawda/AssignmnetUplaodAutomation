import asyncio
import asyncpg
from config import settings

async def check():
    print(f"Connecting to: {settings.database_url}")
    try:
        conn = await asyncpg.connect(settings.database_url)
        print("Connected successfully!")
        
        print("Ensuring tables exist...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id              SERIAL PRIMARY KEY,
                original_name   TEXT        NOT NULL,
                stored_name     TEXT        NOT NULL,
                file_path       TEXT        NOT NULL UNIQUE,
                file_size       BIGINT      NOT NULL DEFAULT 0,
                uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                use_count       INTEGER     NOT NULL DEFAULT 0
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id              SERIAL PRIMARY KEY,
                started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                finished_at     TIMESTAMPTZ,
                triggered_by    TEXT        NOT NULL DEFAULT 'manual',
                status          TEXT        NOT NULL DEFAULT 'running',
                uploads_total   INTEGER     NOT NULL DEFAULT 0,
                log_text        TEXT        NOT NULL DEFAULT '',
                file_id         INTEGER     REFERENCES files(id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS config (
                id                INTEGER     PRIMARY KEY DEFAULT 1,
                username          TEXT        NOT NULL DEFAULT '',
                password_enc      TEXT        NOT NULL DEFAULT '',
                file_id           INTEGER     REFERENCES files(id),
                schedule_time     TEXT        NOT NULL DEFAULT '08:00',
                schedule_enabled  BOOLEAN     NOT NULL DEFAULT FALSE,
                updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        await conn.execute("""
            INSERT INTO config (id) VALUES (1)
            ON CONFLICT (id) DO NOTHING
        """)
        print("Tables checked/created successfully.")
        
        # List tables
        rows = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        print("Current tables in public schema:")
        for r in rows:
            print(f" - {r['table_name']}")
            
        await conn.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(check())
