"""
Pydantic schemas for user management (Admin & shared use).
"""
from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=255)
    role: UserRole
    # Required when creating student or staff
    department_id: str | None = None
    department: str | None = None
    # Student-specific
    roll_number: str | None = None
    course: str | None = None
    semester: str | None = None
    # Staff-specific
    designation: str | None = None


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    is_active: bool | None = None
    avatar_url: str | None = None
    education: str | None = Field(default=None, max_length=255)
    dob: str | None = Field(default=None, max_length=50) # Assuming string format like 'MMM DD, YYYY' for simplicity, matching flutter
    phone: str | None = Field(default=None, max_length=50)
    info: str | None = Field(default=None, max_length=1000)


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    avatar_url: str | None
    education: str | None = None
    dob: str | None = None
    phone: str | None = None
    info: str | None = None


class UserListResponse(BaseModel):
    model_config = {"from_attributes": True}

    users: list[UserResponse]
    total: int
