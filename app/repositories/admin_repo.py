"""
Repository for admin-specific aggregate queries.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.department import Department
from app.schemas.admin import AdminDashboardStats

from app.models.subject import Subject
from app.schemas.subject import SubjectCreate, SubjectResponse

class AdminRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_dashboard_stats(self) -> AdminDashboardStats:
        # ... (lines 16-30)
        students_query = select(func.count(User.id)).where(User.role == UserRole.STUDENT)
        total_students = (await self._db.execute(students_query)).scalar_one()

        hods_query = select(func.count(User.id)).where(User.role == UserRole.HOD)
        total_hods = (await self._db.execute(hods_query)).scalar_one()

        staff_query = select(func.count(User.id)).where(User.role == UserRole.STAFF)
        total_staff = (await self._db.execute(staff_query)).scalar_one()

        dept_query = select(func.count(Department.id))
        total_departments = (await self._db.execute(dept_query)).scalar_one()

        return AdminDashboardStats(
            total_students=total_students,
            total_hods=total_hods,
            total_staff=total_staff,
            total_departments=total_departments
        )

    async def list_subjects(self) -> list[Subject]:
        result = await self._db.execute(select(Subject))
        return result.scalars().all()

    async def create_subject(self, data: SubjectCreate) -> Subject:
        subject = Subject(**data.model_dump())
        self._db.add(subject)
        await self._db.commit()
        await self._db.refresh(subject)
        return subject
