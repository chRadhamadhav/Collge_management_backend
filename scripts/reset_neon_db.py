import asyncio
import sys
import os
from pathlib import Path

# Add project root to pythonpath
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine

async def reset_db():
    confirm = input("This will DELETE ALL TABLES AND TYPES in your Neon database. Are you sure? (y/n): ")
    if confirm.lower() != 'y':
        print("Aborted.")
        return

    async with engine.begin() as conn:
        print("Dropping all tables...")
        # Get all tables in public schema
        res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        for row in res:
            table_name = row[0]
            print(f"Dropping table {table_name}...")
            await conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
        
        print("\nDropping all custom types...")
        # Get all custom enum types in public schema
        res = await conn.execute(text("SELECT t.typname FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE n.nspname = 'public' AND typtype = 'e'"))
        for row in res:
            type_name = row[0]
            print(f"Dropping type {type_name}...")
            await conn.execute(text(f"DROP TYPE IF EXISTS {type_name} CASCADE"))
            
    print("\nDatabase reset successfully.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_db())
