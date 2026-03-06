"""
Pydantic schemas for course materials and categories.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class MaterialCategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    subject_id: str


class MaterialCategoryResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    subject_id: str
    date_created: datetime


class CourseMaterialResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    category_id: str
    file_name: str
    file_url: str
    date_added: datetime
