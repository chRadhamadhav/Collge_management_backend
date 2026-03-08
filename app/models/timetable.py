"""
Timetable model — weekly schedule slots for departments.
"""
import enum
from datetime import time

from sqlalchemy import Enum, ForeignKey, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid


class DayOfWeek(str, enum.Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"


class Timetable(Base):
    __tablename__ = "timetable"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    subject_id: Mapped[str] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    department_id: Mapped[str] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"), nullable=False
    )
    day_of_week: Mapped[DayOfWeek] = mapped_column(Enum(DayOfWeek), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    room: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    subject: Mapped["Subject"] = relationship(back_populates="timetable_slots")  # noqa: F821
    department: Mapped["Department"] = relationship(back_populates="timetable_slots")  # noqa: F821
