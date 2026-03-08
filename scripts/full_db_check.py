import asyncio
import sys
from pathlib import Path

# Add project root to pythonpath
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, inspect
from app.config import get_settings
from app.core.security import hash_password
import uuid

async def full_check():
    settings = get_settings()
    # Use transactional engine
    engine = create_async_engine(settings.database_url, echo=True)
    print(f"--- DB CHECK START: {settings.database_url} ---")
    
    try:
        async with engine.begin() as conn:
            # 1. Inspect Tables
            def get_tables(sync_conn):
                return inspect(sync_conn).get_table_names()
            tables = await conn.run_sync(get_tables)
            print(f"Found Tables: {tables}")
            
            # 2. Check Enums
            res = await conn.execute(text("""
                SELECT t.typname, e.enumlabel 
                FROM pg_enum e 
                JOIN pg_type t ON e.enumtypid = t.oid 
                WHERE t.typname = 'userrole';
            """))
            print(f"userrole enums: {res.fetchall()}")
            
            # 3. Clean up existing (if any)
            await conn.execute(text("DELETE FROM users WHERE email = 'admin'"))
            await conn.execute(text("DELETE FROM departments WHERE name = 'Science & Technology'"))
            
            # 4. Insert Department
            dept_id = str(uuid.uuid4())
            await conn.execute(text("INSERT INTO departments (id, name) VALUES (:id, :name)"), {"id": dept_id, "name": "Science & Technology"})
            
            # 5. Insert Admin
            admin_id = str(uuid.uuid4())
            hashed = hash_password("admin")
            await conn.execute(
                text("INSERT INTO users (id, email, hashed_password, full_name, role, is_active) VALUES (:id, :email, :password, :name, :role, :active)"),
                {"id": admin_id, "email": "admin", "password": hashed, "name": "System Admin", "role": "ADMIN", "active": True}
            )
            print("Inserted Admin and Department")

        # Start a NEW connection to verify persistence
        async with engine.connect() as conn:
            print("--- VERIFYING PERSISTENCE ---")
            res = await conn.execute(text("SELECT email, role FROM users"))
            rows = res.fetchall()
            print(f"Final User Count: {len(rows)}")
            for r in rows:
                print(f"User in DB: {r}")
                
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        await engine.dispose()
    print("--- DB CHECK END ---")

if __name__ == "__main__":
    asyncio.run(full_check())
