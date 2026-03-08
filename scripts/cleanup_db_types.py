import asyncio
import sys
import os
from pathlib import Path

# Add project root to pythonpath
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine
from app.config import get_settings

async def cleanup_types():
    settings = get_settings()
    print(f"Using DATABASE_URL: {settings.database_url}")
    
    types_to_drop = [
        "userrole",
        "announcementtarget",
        "attendancestatus",
        "dayofweek",
        "eventtype"
    ]
    
    async with engine.begin() as conn:
        for type_name in types_to_drop:
            print(f"Dropping type {type_name} if exists...")
            try:
                await conn.execute(text(f"DROP TYPE IF EXISTS {type_name} CASCADE"))
                print(f"Successfully sent DROP command for {type_name}")
            except Exception as e:
                print(f"Error dropping {type_name}: {e}")
                
    await engine.dispose()
    print("Cleanup finished.")

if __name__ == "__main__":
    asyncio.run(cleanup_types())
