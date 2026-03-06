import asyncio
import asyncpg
import uuid
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings

async def fix_student():
    settings = get_settings()
    dsn = settings.database_url.replace("+asyncpg", "")
    conn = await asyncpg.connect(dsn)
    try:
        # Find the student user id
        user = await conn.fetchrow("SELECT id FROM users WHERE email = 'haridasbks1@gmail.com'")
        if not user:
            print("User haridasbks1@gmail.com not found!")
            return
            
        user_id = user['id']
        print(f"User ID: {user_id}")
        
        # See if a profile exists
        prof = await conn.fetchrow("SELECT id FROM students WHERE user_id = $1", user_id)
        if prof:
            print("Profile already exists.")
            return

        # Get any department to link
        dept = await conn.fetchrow("SELECT id FROM departments LIMIT 1")
        if not dept:
            print("No departments found. Please create a department first.")
            return
            
        dept_id = dept['id']
        print(f"Department ID: {dept_id}")
        
        # Insert student profile
        new_id = str(uuid.uuid4())
        await conn.execute(
            "INSERT INTO students (id, user_id, department_id, roll_number, course, semester) VALUES ($1, $2, $3, $4, $5, $6)",
            new_id, user_id, dept_id, "STU-001", "B.Tech Computer Science", "Semester 5"
        )
        print("Successfully created student profile!")
        
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(fix_student())
