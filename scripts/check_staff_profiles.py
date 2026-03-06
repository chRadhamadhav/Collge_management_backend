import asyncio
import asyncpg
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import get_settings

async def check():
    settings = get_settings()
    dsn = settings.database_url.replace("+asyncpg", "")
    conn = await asyncpg.connect(dsn)
    try:
        users = await conn.fetch("SELECT id, email FROM users WHERE role::text ILIKE 'staff'")
        with open("raw_staff_data.txt", "w", encoding="utf-8") as f:
            for u in users:
                uid = u['id']
                prof = await conn.fetchrow("SELECT id FROM staff WHERE user_id = $1", uid)
                if not prof:
                    f.write(f"Staff account {u['email']} is MISSING a profile!\n")
                else:
                    f.write(f"Staff account {u['email']} has profile {prof['id']}\n")
    finally:
        await conn.close()
        
if __name__ == '__main__':
    asyncio.run(check())
