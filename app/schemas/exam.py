"""
Pydantic schemas for exams and exam marks.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class ExamCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    subject_id: str
    department_id: str
    exam_date: datetime
    exam_time: str
    location: str
    invigilator_id: str | None = None
    max_marks: float = Field(gt=0, default=100.0)
    passing_marks: float = Field(gt=0, default=35.0)


class ExamResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    subject_id: str
    department_id: str
    exam_date: datetime
    exam_time: str
    location: str
    invigilator_id: str | None
    max_marks: float
    passing_marks: float
    created_at: datetime
    
class ExamWithSubjectResponse(ExamResponse):
    subject_code: str
    subject_name: str
    invigilator_name: str | None


class ExamMarkEntry(BaseModel):
    """A single student's mark entry — part of a bulk submission."""
    student_id: str
    marks_obtained: float = Field(ge=0)
    is_absent: bool = False


class ExamMarksBulkCreate(BaseModel):
    """Staff submits all marks for an exam in one request."""
    exam_id: str
    marks: list[ExamMarkEntry]


class ExamMarkResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    exam_id: str
    student_id: str
    marks_obtained: float
    is_absent: bool
