from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional

class StaffProfileResponse(BaseModel):
    id: str
    user_id: str
    department_id: str
    designation: str
    
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

class StaffDashboardResponse(BaseModel):
    total_subjects: int
    total_students: int
    total_materials: int
    total_assignments: int
    pending_assignments: int
