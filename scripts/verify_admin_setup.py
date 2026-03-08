import asyncio
import sys
from pathlib import Path

# Add project root to pythonpath
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import get_settings

async def check_admin():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    print(f"Checking {settings.database_url}")
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT email, role, is_active FROM users"))
            users = res.fetchall()
            print(f"Total users: {len(users)}")
            for u in users:
                print(f"User: {u.email}, Role: {u.role}, Active: {u.is_active}")
                
            res = await conn.execute(text("SELECT name FROM departments"))
            depts = res.fetchall()
            print(f"Departments: {[d[0] for d in depts]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_admin())
