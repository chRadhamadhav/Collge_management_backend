import asyncio
import sys
from pathlib import Path

# Add project root to pythonpath
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole

async def test_mapping():
    print(f"Current UserRole enum values: {[e.value for e in UserRole]}")
    async with AsyncSessionLocal() as session:
        try:
            print("Querying for admin user...")
            result = await session.execute(select(User).where(User.email == 'admin'))
            user = result.scalar_one_or_none()
            if user:
                print(f"Found user: {user.email}, Role: {user.role}, Role Value: {user.role.value}")
            else:
                print("User not found (or mapping failed silently?)")
        except Exception as e:
            print(f"MAPPING ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_mapping())
