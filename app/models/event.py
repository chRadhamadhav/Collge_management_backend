"""
Event model — represents academic calendar events like holidays, exams, deadlines.
"""
import enum
from datetime import date, time

from sqlalchemy import Date, Enum, ForeignKey, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class EventType(str, enum.Enum):
    ACADEMIC = "Academic"
    EXTRACURRICULAR = "Extracurricular"
    HOLIDAY = "Holiday"
    DEADLINE = "Deadline"
    ADMIN = "Admin"


class Event(Base, TimestampMixin):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType), nullable=False, default=EventType.ACADEMIC
    )
    
    # If department_id is set, it only applies to that department
    # If null, it's a global college event
    department_id: Mapped[str | None] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"), nullable=True
    )

    department: Mapped["Department"] = relationship()  # noqa: F821
