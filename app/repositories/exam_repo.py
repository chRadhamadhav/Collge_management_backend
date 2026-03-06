"""
Exam repository — queries for exams and exam marks.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.exam import Exam, ExamMark
from app.schemas.exam import ExamCreate, ExamMarksBulkCreate


class ExamRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_exam(self, data: ExamCreate) -> Exam:
        exam = Exam(**data.model_dump())
        self._db.add(exam)
        await self._db.commit()
        await self._db.refresh(exam)
        return exam

    async def get_by_id(self, exam_id: str) -> Exam | None:
        result = await self._db.execute(
            select(Exam).options(selectinload(Exam.marks)).where(Exam.id == exam_id)
        )
        return result.scalar_one_or_none()

    async def list_by_department(self, department_id: str):
        from app.models.subject import Subject
        from app.models.user import User
        from app.models.staff import Staff
        from app.schemas.exam import ExamWithSubjectResponse

        result = await self._db.execute(
            select(Exam, Subject, User.full_name)
            .join(Subject, Exam.subject_id == Subject.id)
            .outerjoin(Staff, Exam.invigilator_id == Staff.id)
            .outerjoin(User, Staff.user_id == User.id)
            .where(Exam.department_id == department_id)
            .order_by(Exam.exam_date.asc())
        )
        
        responses = []
        for exam, subject, invigilator_name in result.all():
            responses.append(ExamWithSubjectResponse(
                id=exam.id,
                name=exam.name,
                subject_id=exam.subject_id,
                department_id=exam.department_id,
                exam_date=exam.exam_date,
                exam_time=exam.exam_time,
                location=exam.location,
                invigilator_id=exam.invigilator_id,
                max_marks=exam.max_marks,
                passing_marks=exam.passing_marks,
                created_at=exam.created_at,
                subject_code=subject.code,
                subject_name=subject.name,
                invigilator_name=invigilator_name
            ))
        return responses
        
    async def assign_invigilator(self, exam_id: str, staff_id: str) -> Exam | None:
        exam = await self.get_by_id(exam_id)
        if exam:
            exam.invigilator_id = staff_id
            await self._db.commit()
            await self._db.refresh(exam)
        return exam

    async def bulk_save_marks(self, data: ExamMarksBulkCreate) -> list[ExamMark]:
        """
        Replace all marks for an exam in one operation.
        Deletes existing marks first to allow re-posting (HOD correction flow).
        """
        existing = await self._db.execute(
            select(ExamMark).where(ExamMark.exam_id == data.exam_id)
        )
        for old_mark in existing.scalars().all():
            await self._db.delete(old_mark)

        new_marks = [
            ExamMark(
                exam_id=data.exam_id,
                student_id=entry.student_id,
                marks_obtained=entry.marks_obtained,
                is_absent=entry.is_absent,
            )
            for entry in data.marks
        ]
        self._db.add_all(new_marks)
        await self._db.commit()
        return new_marks

    async def get_student_results(self, student_id: str) -> list[ExamMark]:
        result = await self._db.execute(
            select(ExamMark)
            .options(selectinload(ExamMark.exam))
            .where(ExamMark.student_id == student_id)
        )
        return result.scalars().all()

    async def get_exam_marks(self, exam_id: str) -> list[ExamMark]:
        result = await self._db.execute(
            select(ExamMark).where(ExamMark.exam_id == exam_id)
        )
        return result.scalars().all()
