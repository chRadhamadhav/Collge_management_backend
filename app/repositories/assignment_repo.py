"""
Assignment repository — queries for assignments and submissions.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assignment import Assignment, AssignmentSubmission
from app.schemas.assignment import AssignmentCreate


class AssignmentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, data: AssignmentCreate, created_by_id: str) -> Assignment:
        assignment = Assignment(
            title=data.title,
            subject_id=data.subject_id,
            target_course=data.target_course,
            due_date=data.due_date,
            max_marks=data.max_marks,
            created_by_id=created_by_id,
        )
        self._db.add(assignment)
        await self._db.flush()

        from app.models.assignment import AssignmentTopic
        for topic_data in data.topics:
            topic = AssignmentTopic(
                assignment_id=assignment.id,
                **topic_data.model_dump(),
            )
            self._db.add(topic)

        await self._db.commit()
        # Fetch with topics to avoid MissingGreenlet error in response mapping
        result = await self._db.execute(
            select(Assignment)
            .options(selectinload(Assignment.topics))
            .where(Assignment.id == assignment.id)
        )
        return result.scalar_one()

    async def get_by_id(self, assignment_id: str) -> Assignment | None:
        result = await self._db.execute(
            select(Assignment)
            .options(selectinload(Assignment.topics))
            .where(Assignment.id == assignment_id)
        )
        return result.scalar_one_or_none()

    async def list_by_subject(self, subject_id: str) -> list[Assignment]:
        result = await self._db.execute(
            select(Assignment)
            .options(selectinload(Assignment.topics))
            .where(Assignment.subject_id == subject_id)
        )
        return result.scalars().all()

    async def list_all(self, subject_ids: list[str]) -> list[Assignment]:
        """List all assignments belonging to the provided subject IDs."""
        result = await self._db.execute(
            select(Assignment)
            .options(selectinload(Assignment.topics))
            .where(Assignment.subject_id.in_(subject_ids))
            .order_by(Assignment.due_date.desc())
        )
        return result.scalars().all()

    async def get_submissions(self, assignment_id: str) -> list[AssignmentSubmission]:
        result = await self._db.execute(
            select(AssignmentSubmission).where(
                AssignmentSubmission.assignment_id == assignment_id
            )
        )
        return result.scalars().all()

    async def submit(self, assignment_id: str, student_id: str, file_url: str) -> AssignmentSubmission:
        submission = AssignmentSubmission(
            assignment_id=assignment_id,
            student_id=student_id,
            file_url=file_url,
        )
        self._db.add(submission)
        await self._db.commit()
        await self._db.refresh(submission)
        return submission

    async def grade_submission(self, submission_id: str, marks: float) -> AssignmentSubmission | None:
        result = await self._db.execute(
            select(AssignmentSubmission).where(AssignmentSubmission.id == submission_id)
        )
        submission = result.scalar_one_or_none()
        if submission:
            submission.marks_given = marks
            await self._db.commit()
            await self._db.refresh(submission)
        return submission

    async def delete(self, assignment: Assignment) -> None:
        await self._db.delete(assignment)
        await self._db.commit()
