import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.api.v1.student import get_student_profile
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_api():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    try:
        async with AsyncSession(engine) as db:
            # Test user ID for haridasbks1@gmail.com
            user_sub = "9cd49515-7a7e-40dc-bcba-c0bb5aeba874"
            current_user = {"sub": user_sub, "role": "student"}
            print(f"Testing profile for {user_sub}")
            
            try:
                res = await get_student_profile(current_user=current_user, db=db)
                print(res)
            except Exception as e:
                import traceback
                traceback.print_exc()
                
            # Test user ID for student@example.com
            user_sub = "e88f583f-1d2f-4886-add4-9da2bc506f0e"
            current_user = {"sub": user_sub, "role": "student"}
            print(f"\nTesting profile for {user_sub}")
            
            try:
                res = await get_student_profile(current_user=current_user, db=db)
                print(res)
            except Exception as e:
                import traceback
                traceback.print_exc()

    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_api())
