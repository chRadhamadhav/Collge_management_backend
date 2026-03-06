"""
Student model — role-specific profile for users with role=student.
Linked 1:1 to a User row.
"""
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class Student(Base, TimestampMixin):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    roll_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    course: Mapped[str | None] = mapped_column(String(255), nullable=True)
    semester: Mapped[str | None] = mapped_column(String(20), nullable=True)
    department_id: Mapped[str] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="student_profile")  # noqa: F821
    department: Mapped["Department"] = relationship(back_populates="students")  # noqa: F821
    attendance_records: Mapped[list["Attendance"]] = relationship(back_populates="student")  # noqa: F821
    exam_marks: Mapped[list["ExamMark"]] = relationship(back_populates="student")  # noqa: F821
    assignment_submissions: Mapped[list["AssignmentSubmission"]] = relationship(back_populates="student")  # noqa: F821
