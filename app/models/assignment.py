"""
Assignment, AssignmentTopic, and AssignmentSubmission models.
Maps directly to the Flutter Assignment/AssignmentTopic/AssignmentSubmission models.
"""
from datetime import datetime

from sqlalchemy import DateTime, Double, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class Assignment(Base, TimestampMixin):
    __tablename__ = "assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_id: Mapped[str] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    target_course: Mapped[str] = mapped_column(String(255), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_marks: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    # Staff who created the assignment — preserved even if staff account is soft-deleted
    created_by_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    subject: Mapped["Subject"] = relationship(back_populates="assignments")  # noqa: F821
    topics: Mapped[list["AssignmentTopic"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan"
    )
    submissions: Mapped[list["AssignmentSubmission"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan"
    )


class AssignmentTopic(Base):
    """A sub-task within an assignment, optionally scoped to a roll number range."""
    __tablename__ = "assignment_topics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    assignment_id: Mapped[str] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    # Roll number range — optional; None means the topic applies to all students
    from_roll_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_roll_no: Mapped[str | None] = mapped_column(String(50), nullable=True)

    assignment: Mapped["Assignment"] = relationship(back_populates="topics")


class AssignmentSubmission(Base, TimestampMixin):
    """A student's submission for an assignment."""
    __tablename__ = "assignment_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    assignment_id: Mapped[str] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    # Marks are null until staff grades the submission
    marks_given: Mapped[float | None] = mapped_column(Double, nullable=True)

    # Relationships
    assignment: Mapped["Assignment"] = relationship(back_populates="submissions")
    student: Mapped["Student"] = relationship(back_populates="assignment_submissions")  # noqa: F821
