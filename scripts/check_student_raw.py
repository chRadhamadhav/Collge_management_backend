import asyncio
import asyncpg
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings

async def query():
    settings = get_settings()
    dsn = settings.database_url.replace("+asyncpg", "")
    conn = await asyncpg.connect(dsn)
    try:
        with open("raw_student_data2.txt", "w", encoding="utf-8") as f:
            profiles = await conn.fetch("SELECT user_id FROM students")
            for p in profiles:
                u_id = p['user_id']
                user = await conn.fetchrow("SELECT email, role::text FROM users WHERE id = $1", u_id)
                if user:
                    f.write(f"Student Profile User -> ID: {u_id} | Email: {user['email']} | Role: {user['role']}\n")
                else:
                    f.write(f"Student Profile User -> ID: {u_id} | MISSING FROM USERS TABLE\n")
    finally:
        await conn.close()
        
if __name__ == '__main__':
    asyncio.run(query())
