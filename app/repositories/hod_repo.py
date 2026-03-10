from datetime import date, timedelta
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.department import Department
from app.models.student import Student
from app.models.staff import Staff
from app.models.subject import Subject
from app.models.timetable import Timetable, DayOfWeek
from app.models.attendance import Attendance, AttendanceStatus
from app.models.exam import Exam, ExamMark
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

        # Use real attendance data
        attendance_data = await self.get_department_attendance_stats(department_id)

        return HODDashboardResponse(
            hod_name=hod_name,
            department_name=department_name.upper(),
            total_students=total_students,
            total_faculty=total_faculty,
            attendance_data=attendance_data,
            faculty_on_duty=on_duty_list,
        )

    async def get_department_subjects(self, department_id: str):
        """Get all subjects for a department."""
        result = await self._db.execute(
            select(Subject).where(Subject.department_id == department_id)
            .order_by(Subject.name)
        )
        return result.scalars().all()

    async def get_department_timetable(self, department_id: str, day: DayOfWeek = None):
        """Get the full timetable for a department, optionally filtered by day."""
        query = select(Timetable).options(selectinload(Timetable.subject))\
            .where(Timetable.department_id == department_id)
        
        if day:
            query = query.where(Timetable.day_of_week == day)
            
        result = await self._db.execute(query.order_by(Timetable.start_time))
        return result.scalars().all()

    async def get_department_students(self, department_id: str):
        """Get all students for a department."""
        from app.models.user import User
        result = await self._db.execute(
            select(Student).options(selectinload(Student.user))
            .where(Student.department_id == department_id)
            .join(User, Student.user_id == User.id)
            .order_by(User.full_name)
        )
        return result.scalars().all()

    async def get_department_attendance_stats(self, department_id: str) -> list[DailyAttendance]:
        """Calculate daily attendance percentages for the last 6 working days (Mon-Sat)."""
        today = date.today()
        # Find the most recent Monday
        days_since_monday = today.weekday()  # Mon=0, Tue=1, ... Sun=6
        monday = today - timedelta(days=days_since_monday)
        
        attendance_list = []
        days_labels = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
        
        # Get all student IDs in the department
        student_ids_res = await self._db.execute(
            select(Student.id).where(Student.department_id == department_id)
        )
        student_ids = student_ids_res.scalars().all()
        total_students = len(student_ids)
        
        if total_students == 0:
            return [DailyAttendance(label=label, value=0.0, active=(label == days_labels[days_since_monday] if days_since_monday < 6 else False)) for label in days_labels]

        for i, label in enumerate(days_labels):
            target_date = monday + timedelta(days=i)
            
            # Count present students for this date in the department
            present_res = await self._db.execute(
                select(func.count(Attendance.id))
                .where(
                    and_(
                        Attendance.student_id.in_(student_ids),
                        Attendance.date == target_date,
                        Attendance.status == AttendanceStatus.PRESENT
                    )
                )
            )
            present_count = present_res.scalar_one()
            
            # Simplified percentage: present records / total students
            percentage = min(1.0, present_count / total_students) if total_students > 0 else 0.0
            
            is_active = (target_date == today)
            attendance_list.append(DailyAttendance(label=label, value=round(percentage, 2), active=is_active))
            
        return attendance_list

    async def get_exam_marks(self, exam_id: str):
        """Fetch all marks for a specific exam."""
        result = await self._db.execute(
            select(ExamMark).options(selectinload(ExamMark.student).selectinload(Student.user))
            .where(ExamMark.exam_id == exam_id)
        )
        return result.scalars().all()
