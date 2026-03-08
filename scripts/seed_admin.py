import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import sys
from pathlib import Path

# Add project root to pythonpath
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.core.security import hash_password
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.department import Department
import uuid

async def seed_admin():
    print("Seeding initial admin and department...")
    async with AsyncSessionLocal() as session:
        # 1. Create a Department first
        dept_id = str(uuid.uuid4())
        dept = Department(
            id=dept_id,
            name="Science & Technology"
        )
        session.add(dept)
        
        # 2. Create Admin User
        admin_user = User(
            id=str(uuid.uuid4()),
            email="admin",
            hashed_password=hash_password("admin"),
            full_name="System Admin",
            role=UserRole.ADMIN,
            is_active=True
        )
        session.add(admin_user)
        
        try:
            await session.commit()
            print("Successfully seeded admin (email: admin, password: admin)")
            print("Successfully seeded department: Science & Technology")
        except Exception as e:
            print(f"Error seeding: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(seed_admin())
