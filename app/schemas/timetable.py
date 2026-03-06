"""
Pydantic schemas for timetable and announcements.
"""
from datetime import datetime, time

from pydantic import BaseModel, Field

from app.models.announcement import AnnouncementTarget
from app.models.timetable import DayOfWeek


# ─── Timetable ───────────────────────────────────────────────────────────────

class TimetableCreate(BaseModel):
    subject_id: str
    department_id: str
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    room: str | None = None


class TimetableResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    subject_id: str
    department_id: str
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    room: str | None


# ─── Announcement ─────────────────────────────────────────────────────────────

class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    body: str = Field(min_length=1)
    target_role: AnnouncementTarget = AnnouncementTarget.ALL


class AnnouncementResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    body: str
    target_role: AnnouncementTarget
    sender_name: str
    created_at: datetime
