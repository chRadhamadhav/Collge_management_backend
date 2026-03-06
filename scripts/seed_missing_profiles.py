import asyncio
import asyncpg
import uuid
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings

async def seed_missing_profiles():
    settings = get_settings()
    dsn = settings.database_url.replace("+asyncpg", "")
    conn = await asyncpg.connect(dsn)
    try:
        # Get all users with role student
        users = await conn.fetch("SELECT id, email FROM users WHERE role::text ILIKE 'student'")
        
        # Get any department
        dept = await conn.fetchrow("SELECT id FROM departments LIMIT 1")
        if not dept:
            print("No departments found. Skipping profile creation.")
            return
            
        dept_id = dept['id']
        
        count = 0
        for u in users:
            user_id = u['id']
            email = u['email']
            
            # Check if profile exists
            prof = await conn.fetchrow("SELECT id FROM students WHERE user_id = $1", user_id)
            if not prof:
                new_id = str(uuid.uuid4())
                await conn.execute(
                    "INSERT INTO students (id, user_id, department_id, roll_number, course, semester) VALUES ($1, $2, $3, $4, $5, $6)",
                    new_id, user_id, dept_id, f"STU-{new_id[:6]}", "B.Tech Computer Science", "Semester 5"
                )
                print(f"Created missing profile for {email}")
                count += 1
                
        print(f"Finished. Created {count} missing profiles.")
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(seed_missing_profiles())
