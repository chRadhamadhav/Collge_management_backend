from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.student import Student
from app.models.user import User
from app.schemas.student import StudentUpdate


class StudentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def update_profile(self, user_id: str, data: StudentUpdate) -> Student | None:
        """Update both User and Student records for a profile."""
        
        # Fetch student with related user
        result = await self._db.execute(
            select(Student)
            .options(selectinload(Student.user), selectinload(Student.department))
            .where(Student.user_id == user_id)
        )
        student = result.scalar_one_or_none()
        
        if not student:
            return None

        # Update User fields
        if data.full_name is not None:
            student.user.full_name = data.full_name
        if data.email is not None:
            student.user.email = data.email
        if data.phone_number is not None:
            student.user.phone = data.phone_number

        # Update Student fields
        if data.course is not None:
            student.course = data.course
        if data.semester is not None:
            student.semester = data.semester

        await self._db.commit()
        await self._db.refresh(student)
        return student
