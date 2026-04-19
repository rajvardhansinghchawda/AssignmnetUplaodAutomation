import asyncio
import asyncpg
from config import settings

async def check():
    conn = await asyncpg.connect(settings.database_url)
    try:
        print("Columns in 'config' table:")
        columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'config'
        """)
        for col in columns:
            print(f" - {col['column_name']} ({col['data_type']})")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check())
