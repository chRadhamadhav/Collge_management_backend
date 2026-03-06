"""
HOD repository — handles queries strictly related to department overviews and HOD dashboard views.
Keeps generic user queries out.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.department import Department
from app.models.student import Student
from app.models.staff import Staff
from app.schemas.hod import HODDashboardResponse, DailyAttendance, FacultyOnDuty


class HODRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_department_by_user_id(self, user_id: str) -> str | None:
        # HODs are stored in the Staff table
        result = await self._db.execute(select(Staff.department_id).where(Staff.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_dashboard_data(self, department_id: str, user_id: str) -> HODDashboardResponse:
        from app.models.user import User
        user_res = await self._db.execute(select(User).where(User.id == user_id))
        user_obj = user_res.scalar_one_or_none()
        hod_name = user_obj.full_name if user_obj else "HOD"

        # Get Department Name
        dept_res = await self._db.execute(select(Department).where(Department.id == department_id))
        dept = dept_res.scalar_one_or_none()
        department_name = dept.name if dept else "Unknown Department"

        # Count Students
        student_res = await self._db.execute(
            select(func.count(Student.id)).where(Student.department_id == department_id)
        )
        total_students = student_res.scalar_one()

        # Count Faculty
        staff_res = await self._db.execute(
            select(func.count(Staff.id)).where(Staff.department_id == department_id)
        )
        total_faculty = staff_res.scalar_one()

        # Faculty on Duty 
        # For now, pull up to 2 random active staff in the department
        duty_res = await self._db.execute(
            select(Staff).where(Staff.department_id == department_id)
            .options(selectinload(Staff.user))
            .limit(2)
        )
        staff_members = duty_res.scalars().all()
        
        on_duty_list = []
        for staff in staff_members:
            on_duty_list.append(FacultyOnDuty(
                name=staff.user.full_name,
                role=staff.designation.upper()
            ))

        # Static Mock for Attendance Data until attendance logging is heavily populated
        attendance_data = [
            DailyAttendance(label="MON", value=0.55, active=False),
            DailyAttendance(label="TUE", value=0.45, active=False),
            DailyAttendance(label="WED", value=0.65, active=False),
            DailyAttendance(label="THU", value=0.94, active=True),
            DailyAttendance(label="FRI", value=0.40, active=False),
            DailyAttendance(label="SAT", value=0.30, active=False),
        ]

        return HODDashboardResponse(
            hod_name=hod_name,
            department_name=department_name.upper(),
            total_students=total_students,
            total_faculty=total_faculty,
            attendance_data=attendance_data,
            faculty_on_duty=on_duty_list,
        )
