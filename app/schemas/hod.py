"""
Pydantic schemas specifically for the HOD module.
"""
from pydantic import BaseModel

class DailyAttendance(BaseModel):
    label: str
    value: float
    active: bool

class FacultyOnDuty(BaseModel):
    name: str
    role: str

class HODDashboardResponse(BaseModel):
    hod_name: str
    department_name: str
    total_students: int
    total_faculty: int
    attendance_data: list[DailyAttendance]
    faculty_on_duty: list[FacultyOnDuty]

class StaffMemberResponse(BaseModel):
    id: str
    name: str

class FacultyDutyResponse(BaseModel):
    name: str
    status: str
    badge: str
    timeSlot: str
    location: str

class HODProfileResponse(BaseModel):
    name: str
    email: str
    phone: str | None
    avatar_url: str | None
    employee_id: str
    department_name: str
    qualifications: str | None
    designation: str

class HODSubjectResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    name: str
    code: str

class HODTimetableResponse(BaseModel):
    id: str
    subject_id: str
    subject_name: str
    subject_code: str
    day_of_week: str
    start_time: str
    end_time: str
    room: str

class HODStudentResponse(BaseModel):
    id: str
    name: str
    roll_number: str
    avatar_url: str | None

class HODExamMarkResponse(BaseModel):
    id: str
    student_id: str
    student_name: str
    roll_number: str
    marks_obtained: float
    is_absent: bool
