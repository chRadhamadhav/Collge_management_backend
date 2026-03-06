"""
Subject model — a course/paper taught by a staff member in a department.
"""
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    department_id: Mapped[str] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )
    staff_id: Mapped[str | None] = mapped_column(
        ForeignKey("staff.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    department: Mapped["Department"] = relationship(back_populates="subjects")  # noqa: F821
    staff: Mapped["Staff"] = relationship(back_populates="subjects")  # noqa: F821
    exams: Mapped[list["Exam"]] = relationship(back_populates="subject")  # noqa: F821
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="subject")  # noqa: F821
    material_categories: Mapped[list["MaterialCategory"]] = relationship(back_populates="subject")  # noqa: F821
    attendance_records: Mapped[list["Attendance"]] = relationship(back_populates="subject")  # noqa: F821
    timetable_slots: Mapped[list["Timetable"]] = relationship(back_populates="subject")  # noqa: F821
