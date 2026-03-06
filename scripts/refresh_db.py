import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings
from app.models.base import Base
from app.database import AsyncSessionLocal
from app.core.security import hash_password

# Import all models to register with Base.metadata before creating tables
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.student import Student
from app.models.staff import Staff
from app.models.announcement import Announcement
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.attendance import Attendance
from app.models.exam import Exam, ExamMark
from app.models.material import MaterialCategory, CourseMaterial
from app.models.subject import Subject
from app.models.timetable import Timetable

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=True,
    pool_pre_ping=True
)

async def refresh():
    print("Connecting to database:", settings.database_url)
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        
    print("Creating all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Seeding admin user...")
    async with AsyncSessionLocal() as session:
        admin_user = User(
            email="admin@college.com",
            hashed_password=hash_password("adminpass"),
            full_name="System Admin",
            role=UserRole.ADMIN,
            is_active=True
        )
        session.add(admin_user)
        await session.commit()
        
    print("Done! Database tables refreshed.")
    print("Admin Email: admin@college.com")
    print("Admin Password: adminpass")

if __name__ == "__main__":
    asyncio.run(refresh())
