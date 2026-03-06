"""
Department model.
Represents an academic department; each HOD manages one department.
"""
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # HOD who heads this department (nullable — department may be created before HOD assignment)
    hod_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    students: Mapped[list["Student"]] = relationship(back_populates="department")  # noqa: F821
    staff_members: Mapped[list["Staff"]] = relationship(back_populates="department")  # noqa: F821
    subjects: Mapped[list["Subject"]] = relationship(back_populates="department")  # noqa: F821
    timetable_slots: Mapped[list["Timetable"]] = relationship(back_populates="department")  # noqa: F821
