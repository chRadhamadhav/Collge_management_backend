import asyncio
import asyncpg
import sys
from pathlib import Path

# Add project root to pythonpath
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings

async def check_enums():
    settings = get_settings()
    dsn = settings.database_url.replace("postgresql+asyncpg://", "postgres://")
    conn = await asyncpg.connect(dsn)
    try:
        query = """
        SELECT t.typname, e.enumlabel 
        FROM pg_enum e 
        JOIN pg_type t ON e.enumtypid = t.oid 
        ORDER BY t.typname, e.enumsortorder;
        """
        rows = await conn.fetch(query)
        for r in rows:
            print(f"Type: {r['typname']}, Label: {r['enumlabel']}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_enums())
