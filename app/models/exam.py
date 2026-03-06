"""
Exam and ExamMark models.
An Exam belongs to a Subject. ExamMark records one student's score per exam.
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Double, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class Exam(Base, TimestampMixin):
    __tablename__ = "exams"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_id: Mapped[str] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    department_id: Mapped[str] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )
    exam_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    exam_time: Mapped[str] = mapped_column(String(50), nullable=False, default="10:00 AM - 01:00 PM")
    location: Mapped[str] = mapped_column(String(255), nullable=False, default="TBA")
    invigilator_id: Mapped[str | None] = mapped_column(
        ForeignKey("staff.id", ondelete="SET NULL"), nullable=True
    )
    max_marks: Mapped[float] = mapped_column(Double, nullable=False, default=100.0)
    passing_marks: Mapped[float] = mapped_column(Double, nullable=False, default=35.0)

    # Relationships
    subject: Mapped["Subject"] = relationship(back_populates="exams")  # noqa: F821
    invigilator: Mapped["Staff"] = relationship()  # noqa: F821
    marks: Mapped[list["ExamMark"]] = relationship(back_populates="exam", cascade="all, delete-orphan")


class ExamMark(Base):
    """Records a single student's performance in a single exam."""
    __tablename__ = "exam_marks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    exam_id: Mapped[str] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    marks_obtained: Mapped[float] = mapped_column(Double, nullable=False, default=0.0)
    is_absent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    exam: Mapped["Exam"] = relationship(back_populates="marks")
    student: Mapped["Student"] = relationship(back_populates="exam_marks")  # noqa: F821
