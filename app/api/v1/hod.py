"""
HOD routes — department management: timetable, exams, announcements, results.
Restricted to users with role=hod.
"""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role
from app.repositories.exam_repo import ExamRepository
from app.schemas.exam import ExamCreate, ExamMarksBulkCreate, ExamMarkResponse, ExamResponse, ExamWithSubjectResponse
from app.schemas.timetable import AnnouncementCreate, AnnouncementResponse, TimetableCreate, TimetableResponse
from app.repositories.hod_repo import HODRepository
from app.schemas.hod import HODDashboardResponse, StaffMemberResponse, HODSubjectResponse, HODTimetableResponse, HODStudentResponse, HODExamMarkResponse
from app.core.exceptions import ForbiddenError

router = APIRouter(prefix="/hod", tags=["hod"])

HODOnly = Annotated[dict, Depends(require_role("hod", "admin"))]

@router.get("/dashboard/", response_model=HODDashboardResponse)
async def get_hod_dashboard(
    current_user: HODOnly,
    db: AsyncSession = Depends(get_db),
) -> HODDashboardResponse:
    """Get the dashboard overview statistics for the HOD's department."""
    repo = HODRepository(db)
    
    department_id = await repo.get_department_by_user_id(current_user["sub"])
    if not department_id:
        raise ForbiddenError("HOD profile not found or department not assigned.")
        
    return await repo.get_dashboard_data(department_id, current_user["sub"])



@router.post("/exams/", response_model=ExamResponse, status_code=201)
async def create_exam(
    data: ExamCreate,
    _: HODOnly,
    db: AsyncSession = Depends(get_db),
) -> ExamResponse:
    """Create a new exam for a subject."""
    repo = ExamRepository(db)
    return await repo.create_exam(data)


@router.get("/exams/", response_model=list[ExamWithSubjectResponse])
async def list_exams(
    current_user: HODOnly,
    db: AsyncSession = Depends(get_db),
) -> list[ExamWithSubjectResponse]:
    """List all exams for the HOD's department."""
    from app.core.exceptions import ForbiddenError
    hod_repo = HODRepository(db)
    department_id = await hod_repo.get_department_by_user_id(current_user["sub"])
    if not department_id:
        raise ForbiddenError("HOD profile not found or department not assigned.")

    exam_repo = ExamRepository(db)
    return await exam_repo.list_by_department(department_id)

@router.get("/faculty/", response_model=list[StaffMemberResponse])
async def list_department_faculty(
    current_user: HODOnly,
    db: AsyncSession = Depends(get_db),
) -> list[StaffMemberResponse]:
    """List all faculty members in the HOD's department."""
    from app.core.exceptions import ForbiddenError
    from sqlalchemy import select
    from app.models.staff import Staff
    from app.models.user import User

    hod_repo = HODRepository(db)
    department_id = await hod_repo.get_department_by_user_id(current_user["sub"])
    if not department_id:
        raise ForbiddenError("HOD profile not found or department not assigned.")

    result = await db.execute(
        select(Staff.id, User.full_name)
        .join(User, Staff.user_id == User.id)
        .where(Staff.department_id == department_id)
        .order_by(User.full_name)
    )
    return [{"id": row.id, "name": row.full_name} for row in result.all()]


from app.schemas.hod import FacultyDutyResponse, HODProfileResponse

@router.get("/profile/", response_model=HODProfileResponse)
async def get_hod_profile(
    current_user: HODOnly,
    db: AsyncSession = Depends(get_db),
) -> HODProfileResponse:
    """Get the full profile details for the HOD."""
    from app.core.exceptions import ForbiddenError
    from sqlalchemy import select
    from app.models.user import User
    from app.models.staff import Staff
    from app.models.department import Department
    
    result = await db.execute(
        select(User, Staff, Department)
        .join(Staff, User.id == Staff.user_id)
        .join(Department, Staff.department_id == Department.id)
        .where(User.id == current_user["sub"])
    )
    row = result.first()
    if not row:
        raise ForbiddenError("HOD profile not found.")
        
    user, staff, dept = row
    
    return HODProfileResponse(
        name=user.full_name,
        email=user.email,
        phone=user.phone or "+1 234 567 890", # Default mock if none
        avatar_url=user.avatar_url,
        employee_id=staff.id[:12], # Truncate for UI
        department_name=dept.name,
        qualifications=user.education,
        designation="HEAD OF DEPARTMENT"
    )

@router.get("/faculty/duty/", response_model=list[FacultyDutyResponse])
async def list_faculty_on_duty(
    current_user: HODOnly,
    db: AsyncSession = Depends(get_db),
) -> list[FacultyDutyResponse]:
    """List all faculty currently assigned to invigilation duty."""
    from app.core.exceptions import ForbiddenError
    from sqlalchemy import select
    from app.models.exam import Exam
    from app.models.staff import Staff
    from app.models.user import User
    from app.models.subject import Subject
    from datetime import date
    import pytz
    
    hod_repo = HODRepository(db)
    department_id = await hod_repo.get_department_by_user_id(current_user["sub"])
    if not department_id:
        raise ForbiddenError("HOD profile not found or department not assigned.")

    # Get today's active exams that have an invigilator assigned
    today = date.today()
    result = await db.execute(
        select(User.full_name, Exam.exam_time, Exam.location, Subject.name)
        .select_from(Exam)
        .join(Subject, Exam.subject_id == Subject.id)
        .join(Staff, Exam.invigilator_id == Staff.id)
        .join(User, Staff.user_id == User.id)
        .where(Exam.department_id == department_id)
        .where(Exam.invigilator_id.isnot(None))
    )
    
    duty_list = []
    for full_name, time_str, location, subject_name in result.all():
        duty_list.append(FacultyDutyResponse(
            name=full_name,
            status="ASSIGNED TO DUTY",
            badge="INVIGILATION",
            timeSlot=time_str or "TBD",
            location=location or "TBD",
        ))
    
    return duty_list

from pydantic import BaseModel
class AssignInvigilatorRequest(BaseModel):
    staff_id: str

@router.patch("/exams/{exam_id}/assign/", response_model=ExamResponse)
async def assign_invigilator(
    exam_id: str,
    data: AssignInvigilatorRequest,
    _: HODOnly,
    db: AsyncSession = Depends(get_db),
) -> ExamResponse:
    """Assign an invigilator to an exam."""
    from app.core.exceptions import NotFoundError
    repo = ExamRepository(db)
    exam = await repo.assign_invigilator(exam_id, data.staff_id)
    if not exam:
        raise NotFoundError("Exam", exam_id)
    return exam


@router.post("/exams/{exam_id}/results/", response_model=list[ExamMarkResponse])
async def post_results(
    exam_id: str,
    data: ExamMarksBulkCreate,
    _: HODOnly,
    db: AsyncSession = Depends(get_db),
) -> list[ExamMarkResponse]:
    """Post or update exam results in bulk. Replaces existing marks for the exam."""
    repo = ExamRepository(db)
    return await repo.bulk_save_marks(data)


@router.get("/exams/{exam_id}/marks/", response_model=list[HODExamMarkResponse])
async def get_exam_marks(
    exam_id: str,
    _: HODOnly,
    db: AsyncSession = Depends(get_db),
) -> list[HODExamMarkResponse]:
    """Get all marks for a specific exam with student details."""
    hod_repo = HODRepository(db)
    marks = await hod_repo.get_exam_marks(exam_id)
    
    return [
        HODExamMarkResponse(
            id=m.id,
            student_id=m.student_id,
            student_name=m.student.user.full_name,
            roll_number=m.student.roll_number,
            marks_obtained=m.marks_obtained,
            is_absent=m.is_absent
        ) for m in marks
    ]


@router.post("/timetable/", response_model=TimetableResponse, status_code=201)
async def create_timetable_slot(
    data: TimetableCreate,
    _: HODOnly,
    db: AsyncSession = Depends(get_db),
) -> TimetableResponse:
    """Add a new timetable slot for a department."""
    from app.models.timetable import Timetable
    slot = Timetable(**data.model_dump())
    db.add(slot)
    await db.commit()
    await db.refresh(slot)
    return slot


@router.post("/announcements/", response_model=AnnouncementResponse, status_code=201)
async def create_announcement(
    data: AnnouncementCreate,
    current_user: HODOnly,
    db: AsyncSession = Depends(get_db),
) -> AnnouncementResponse:
    """Broadcast an announcement to a target audience."""
    from app.models.announcement import Announcement
    from app.models.user import User
    
    announcement = Announcement(
        **data.model_dump(),
        created_by_id=current_user["sub"],
    )
    db.add(announcement)
    await db.commit()
    await db.refresh(announcement)
    
    # Fetch the user's name
    user_res = await db.execute(select(User.full_name).where(User.id == current_user["sub"]))
    sender_name = user_res.scalar_one_or_none() or "Admin"
    
    # Return a Pydantic dict that matches the schema
    return AnnouncementResponse(
        id=announcement.id,
        title=announcement.title,
        body=announcement.body,
        target_role=announcement.target_role,
        created_at=announcement.created_at,
        sender_name=sender_name,
    )


@router.get("/announcements/", response_model=list[AnnouncementResponse])
async def list_announcements(
    _: HODOnly,
    db: AsyncSession = Depends(get_db),
) -> list[AnnouncementResponse]:
    """List all announcements created within the HOD's scope."""
    from sqlalchemy import select
    from app.models.announcement import Announcement
    from app.models.user import User
    
    result = await db.execute(
        select(Announcement, User.full_name)
        .join(User, Announcement.created_by_id == User.id)
        .order_by(Announcement.created_at.desc())
    )
    
    responses = []
    for ann, sender_name in result.all():
        responses.append(AnnouncementResponse(
            id=ann.id,
            title=ann.title,
            body=ann.body,
            target_role=ann.target_role,
            created_at=ann.created_at,
            sender_name=sender_name,
        ))
    return responses


@router.delete("/announcements/{announcement_id}/", status_code=204)
async def delete_announcement(
    announcement_id: str,
    _: HODOnly,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an announcement by ID."""
    from sqlalchemy import select
    from app.core.exceptions import NotFoundError
    from app.models.announcement import Announcement
    result = await db.execute(select(Announcement).where(Announcement.id == announcement_id))
    ann = result.scalar_one_or_none()
    if not ann:
        raise NotFoundError("Announcement", announcement_id)
    await db.delete(ann)
    await db.commit()

@router.get("/subjects/", response_model=list[HODSubjectResponse])
async def list_department_subjects(
    current_user: HODOnly,
    db: AsyncSession = Depends(get_db),
) -> list[HODSubjectResponse]:
    """List all subjects in the HOD's department."""
    repo = HODRepository(db)
    department_id = await repo.get_department_by_user_id(current_user["sub"])
    if not department_id:
        raise ForbiddenError("HOD profile not found or department not assigned.")
    
    return await repo.get_department_subjects(department_id)

@router.get("/students/", response_model=list[HODStudentResponse])
async def list_department_students(
    current_user: HODOnly,
    db: AsyncSession = Depends(get_db),
) -> list[HODStudentResponse]:
    """List all students in the HOD's department."""
    repo = HODRepository(db)
    department_id = await repo.get_department_by_user_id(current_user["sub"])
    if not department_id:
        raise ForbiddenError("HOD profile not found or department not assigned.")
    
    students = await repo.get_department_students(department_id)
    return [
        HODStudentResponse(
            id=s.id,
            name=s.user.full_name,
            roll_number=s.roll_number,
            avatar_url=s.user.avatar_url
        ) for s in students
    ]

@router.get("/timetable/", response_model=list[HODTimetableResponse])
async def get_department_timetable(
    current_user: HODOnly,
    day_of_week: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[HODTimetableResponse]:
    """Get the weekly timetable for the department."""
    from app.models.timetable import DayOfWeek
    repo = HODRepository(db)
    department_id = await repo.get_department_by_user_id(current_user["sub"])
    if not department_id:
        raise ForbiddenError("HOD profile not found or department not assigned.")
    
    day_enum = None
    if day_of_week:
        day_enum = DayOfWeek(day_of_week.upper())
        
    slots = await repo.get_department_timetable(department_id, day_enum)
    
    # Transform to include subject name/code for UI convenience
    responses = []
    for slot in slots:
        responses.append(HODTimetableResponse(
            id=slot.id,
            subject_id=slot.subject_id,
            subject_name=slot.subject.name,
            subject_code=slot.subject.code,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time.strftime("%H:%M"),
            end_time=slot.end_time.strftime("%H:%M"),
            room=slot.room or "TBD"
        ))
    return responses

    return responses
