from pydantic import BaseModel

class AdminDashboardStats(BaseModel):
    total_students: int
    total_hods: int
    total_staff: int
    total_departments: int
