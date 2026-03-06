"""
Pydantic schemas for attendance.
"""
from datetime import date

from pydantic import BaseModel

from app.models.attendance import AttendanceStatus


class AttendanceRecord(BaseModel):
    student_id: str
    status: AttendanceStatus


class AttendanceBulkCreate(BaseModel):
    """Staff submits attendance for the whole class in one request."""
    subject_id: str
    date: date
    records: list[AttendanceRecord]


class AttendanceSummary(BaseModel):
    """Attendance summary returned to a student for a given subject."""
    subject_id: str
    subject_name: str
    total_classes: int
    attended: int
    absent: int
    percentage: float
