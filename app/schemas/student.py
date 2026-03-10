from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.schemas.user import UserResponse

class StudentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    user_id: str
    roll_number: str
    course: str
    semester: str
    department_id: str
    
    user: UserResponse

class StudentProfileResponse(BaseModel):
    id: str
    user_id: str
    department_id: str
    roll_number: str
    course: Optional[str] = None
    semester: Optional[str] = None
    
    # Merged from User
    email: str
    full_name: str
    phone_number: Optional[str] = None
    role: str
    is_active: bool
    avatar_url: Optional[str] = None
    
    # Merged from Department
    department_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    course: Optional[str] = None
    semester: Optional[str] = None

class StudentDashboardResponse(BaseModel):
    attendance_percentage: float
    total_assignments: int
    pending_assignments: int
    upcoming_exams: int
