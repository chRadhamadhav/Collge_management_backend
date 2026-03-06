"""
Attendance repository — queries for attendance records.
Enforces the unique-per-day constraint via upsert-style logic.
"""
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance, AttendanceStatus
from app.schemas.attendance import AttendanceBulkCreate


class AttendanceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def bulk_upsert(self, data: AttendanceBulkCreate) -> list[Attendance]:
        """
        Save attendance for a full class in one operation.
        If a record for (student, subject, date) already exists, it is updated.
        New records are inserted. This prevents duplicate entries if staff
        accidentally submits twice.
        """
        upserted: list[Attendance] = []

        for record in data.records:
            existing = await self._db.execute(
                select(Attendance).where(
                    Attendance.student_id == record.student_id,
                    Attendance.subject_id == data.subject_id,
                    Attendance.date == data.date,
                )
            )
            row = existing.scalar_one_or_none()

            if row:
                row.status = record.status
                upserted.append(row)
            else:
                new_record = Attendance(
                    student_id=record.student_id,
                    subject_id=data.subject_id,
                    date=data.date,
                    status=record.status,
                )
                self._db.add(new_record)
                upserted.append(new_record)

        await self._db.commit()
        return upserted

    async def get_student_summary(self, student_id: str) -> list[dict]:
        """
        Returns per-subject attendance counts for a student.
        Used to populate the student's attendance screen.
        """
        result = await self._db.execute(
            select(Attendance).where(Attendance.student_id == student_id)
        )
        records = result.scalars().all()

        # Group by subject_id
        by_subject: dict[str, dict] = {}
        for r in records:
            if r.subject_id not in by_subject:
                by_subject[r.subject_id] = {"total": 0, "attended": 0, "absent": 0}
            by_subject[r.subject_id]["total"] += 1
            if r.status == AttendanceStatus.PRESENT:
                by_subject[r.subject_id]["attended"] += 1
            elif r.status == AttendanceStatus.ABSENT:
                by_subject[r.subject_id]["absent"] += 1

        return [{"subject_id": sid, **counts} for sid, counts in by_subject.items()]
