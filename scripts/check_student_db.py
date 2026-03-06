import asyncio
import os
import sys
from pathlib import Path

# Add project root to pythonpath
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import get_settings

async def test_db():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as conn:
        print("Users:")
        res = await conn.execute(text("SELECT id, email, role FROM users WHERE role = 'student'"))
        for r in res:
            print(f"User: {dict(r._mapping)}")
            
        print("\nStudents:")
        res = await conn.execute(text("SELECT id, user_id, department_id, course FROM students"))
        for r in res:
            print(f"Student: {dict(r._mapping)}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_db())
