"""
Pydantic schemas for assignments and submissions.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class AssignmentTopicCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=1, max_length=1000)
    from_roll_no: str | None = None
    to_roll_no: str | None = None


class AssignmentCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    subject_id: str
    target_course: str
    due_date: datetime
    max_marks: int = Field(gt=0, default=100)
    topics: list[AssignmentTopicCreate]


class AssignmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    due_date: datetime | None = None
    max_marks: int | None = Field(default=None, gt=0)


class AssignmentTopicResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    description: str
    from_roll_no: str | None
    to_roll_no: str | None


class AssignmentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    subject_id: str
    target_course: str
    due_date: datetime
    max_marks: int
    topics: list[AssignmentTopicResponse]
    created_at: datetime


class SubmissionGrade(BaseModel):
    """Payload for staff to grade a student's submission."""
    marks_given: float = Field(ge=0)
