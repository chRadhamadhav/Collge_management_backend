"""
Repository for admin-specific aggregate queries.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.department import Department
from app.schemas.admin import AdminDashboardStats

class AdminRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_dashboard_stats(self) -> AdminDashboardStats:
        # Count students
        students_query = select(func.count(User.id)).where(User.role == UserRole.STUDENT)
        total_students = (await self._db.execute(students_query)).scalar_one()

        # Count HODs
        hods_query = select(func.count(User.id)).where(User.role == UserRole.HOD)
        total_hods = (await self._db.execute(hods_query)).scalar_one()

        # Count Staff
        staff_query = select(func.count(User.id)).where(User.role == UserRole.STAFF)
        total_staff = (await self._db.execute(staff_query)).scalar_one()

        # Count Departments
        dept_query = select(func.count(Department.id))
        total_departments = (await self._db.execute(dept_query)).scalar_one()

        return AdminDashboardStats(
            total_students=total_students,
            total_hods=total_hods,
            total_staff=total_staff,
            total_departments=total_departments
        )
