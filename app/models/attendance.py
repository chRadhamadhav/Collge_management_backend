"""
Attendance model — daily presence/absence record per student per subject.
Status mirrors the Flutter AttendanceStatus enum.
"""
import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    PENDING = "PENDING"


class Attendance(Base, TimestampMixin):
    __tablename__ = "attendance"
    __table_args__ = (
        # A student can only have one attendance record per subject per day
        UniqueConstraint("student_id", "subject_id", "date", name="uq_attendance_student_subject_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[str] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus), nullable=False, default=AttendanceStatus.PENDING
    )

    # Relationships
    student: Mapped["Student"] = relationship(back_populates="attendance_records")  # noqa: F821
    subject: Mapped["Subject"] = relationship(back_populates="attendance_records")  # noqa: F821
