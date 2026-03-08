import asyncio
import asyncpg
import uuid
import sys
from pathlib import Path

# Add project root to pythonpath
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.security import hash_password
from app.config import get_settings

async def direct_seed():
    settings = get_settings()
    dsn = settings.database_url.replace("postgresql+asyncpg://", "postgres://")
    print(f"Connecting to {dsn}")
    conn = await asyncpg.connect(dsn)
    try:
        # 1. Create Department
        dept_id = str(uuid.uuid4())
        await conn.execute("INSERT INTO departments (id, name) VALUES ($1, $2)", dept_id, "Science & Technology")
        
        # 2. Create Admin
        admin_id = str(uuid.uuid4())
        hashed = hash_password("admin")
        await conn.execute(
            "INSERT INTO users (id, email, hashed_password, full_name, role, is_active) VALUES ($1, $2, $3, $4, $5, $6)",
            admin_id, "admin", hashed, "System Admin", "ADMIN", True
        )
        print("Inserted Admin and Department via asyncpg")
        
        # 3. Check count
        count = await conn.fetchval("SELECT count(*) FROM users")
        print(f"User count now: {count}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(direct_seed())
