import asyncio
import asyncpg
import sys
import os

# Add current directory to path so we can import config
sys.path.append(os.getcwd())

from config import settings

async def check():
    try:
        conn = await asyncpg.connect(settings.database_url)
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    try:
        print("Checking 'config' table...")
        # Check if table exists
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'config'
            )
        """)
        if not exists:
            print("Table 'config' does not exist.")
            return

        columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'config'
        """)
        print("Columns:")
        for col in columns:
            print(f" - {col['column_name']} ({col['data_type']})")
        
        count = await conn.fetchval("SELECT count(*) FROM config")
        print(f"Total rows: {count}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check())
