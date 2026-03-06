import asyncio
import os
import sys

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from app.config import get_settings
from app.models.base import Base

# Ensure all models are loaded
import app.models

async def create_tables():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.begin() as conn:
            print("Running create_all()...")
            await conn.run_sync(Base.metadata.create_all)
            print("Successfully created missing tables.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())
