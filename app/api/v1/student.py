"""
Student routes — read-only views of courses, attendance, assignments, results.
Restricted to users with role=student.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role
from app.core.exceptions import NotFoundError
from app.repositories.assignment_repo import AssignmentRepository
from app.repositories.attendance_repo import AttendanceRepository
from app.repositories.exam_repo import ExamRepository
from app.repositories.material_repo import MaterialRepository
from app.schemas.attendance import AttendanceSummary
from app.schemas.exam import ExamMarkResponse
from app.schemas.assignment import AssignmentResponse
from app.schemas.timetable import TimetableResponse
from app.schemas.student import StudentProfileResponse, StudentDashboardResponse
from app.schemas.material import MaterialCategoryResponse
from app.schemas.event import EventResponse

router = APIRouter(prefix="/student", tags=["student"])

StudentAccess = Annotated[dict, Depends(require_role("student", "staff", "hod", "admin"))]

# ─── Profile & Dashboard ──────────────────────────────────────────────────────

@router.get("/profile/", response_model=StudentProfileResponse)
async def get_student_profile(
    current_user: StudentAccess,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the profile details for the currently logged-in student."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.student import Student

    result = await db.execute(
        select(Student)
        .options(selectinload(Student.user), selectinload(Student.department))
        .where(Student.user_id == current_user["sub"])
    )
    student = result.scalar_one_or_none()
    
    if not student:
        raise NotFoundError("Student Profile", current_user["sub"])

    return {
        "id": student.id,
        "user_id": student.user_id,
        "department_id": student.department_id,
        "roll_number": student.roll_number,
        "course": student.course,
        "semester": student.semester,
        "email": student.user.email,
        "full_name": student.user.full_name,
        "phone_number": student.user.phone,
        "role": student.user.role.value,
        "is_active": student.user.is_active,
        "avatar_url": student.user.avatar_url,
        "department_name": student.department.name if student.department else None,
    }


@router.get("/dashboard/", response_model=StudentDashboardResponse)
async def get_student_dashboard(
    current_user: StudentAccess,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get aggregate statistics for the dashboard of the logged-in student."""
    from sqlalchemy import select, func
    from sqlalchemy.orm import selectinload
    from app.models.student import Student
    from app.models.assignment import Assignment
    from app.models.exam import Exam

    # 1. Get student
    result = await db.execute(select(Student).where(Student.user_id == current_user["sub"]))
    student = result.scalar_one_or_none()
    
    if not student:
        raise NotFoundError("Student Profile", current_user["sub"])

    # Wait to fetch various metrics concurrently or sequentially
    repo = AttendanceRepository(db)
    raw = await repo.get_student_summary(student.id)
    
    # Calculate overall attendance %
    total_classes = sum(entry["total"] for entry in raw)
    attended_classes = sum(entry["attended"] for entry in raw)
    attendance_percentage = round((attended_classes / total_classes * 100), 1) if total_classes > 0 else 0.0

    # Total & Pending Assignments
    # We load all assignments for their course. We could also join submissions to find 'pending' precisely.
    assignments_res = await db.execute(select(Assignment).where(Assignment.target_course == student.course).options(selectinload(Assignment.submissions)))
    all_assignments = assignments_res.scalars().unique().all()
    
    total_assignments = len(all_assignments)
    
    # Check if student has a submission for each
    pending_assignments = 0
    for a in all_assignments:
        has_submitted = any(sub.student_id == student.id for sub in a.submissions)
        if not has_submitted:
            pending_assignments += 1
            
    # Upcoming exams
    exams_res = await db.execute(select(func.count(Exam.id)).where(Exam.department_id == student.department_id))
    upcoming_exams = exams_res.scalar_one_or_none() or 0

    return {
        "attendance_percentage": attendance_percentage,
        "total_assignments": total_assignments,
        "pending_assignments": pending_assignments,
        "upcoming_exams": upcoming_exams,
    }


# ─── Academic ─────────────────────────────────────────────────────────────────

@router.get("/attendance/", response_model=list[dict])
async def my_attendance(
    current_user: StudentAccess,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """
    Return per-subject attendance summary for the authenticated student.
    Percentage is calculated server-side to keep frontend presentation-only.
    """
    from sqlalchemy import select
    from app.models.student import Student

    result = await db.execute(select(Student).where(Student.user_id == current_user["sub"]))
    student = result.scalar_one_or_none()
    if not student:
        raise NotFoundError("Student profile", current_user["sub"])

    repo = AttendanceRepository(db)
    raw = await repo.get_student_summary(student.id)

    # Compute percentage here so Flutter just renders the number
    for entry in raw:
        total = entry["total"]
        entry["percentage"] = round((entry["attended"] / total * 100), 1) if total > 0 else 0.0

    return raw


@router.get("/results/", response_model=list[ExamMarkResponse])
async def my_results(
    current_user: StudentAccess,
    db: AsyncSession = Depends(get_db),
) -> list[ExamMarkResponse]:
    """Return all exam results for the authenticated student."""
    from sqlalchemy import select
    from app.models.student import Student

    result = await db.execute(select(Student).where(Student.user_id == current_user["sub"]))
    student = result.scalar_one_or_none()
    if not student:
        raise NotFoundError("Student profile", current_user["sub"])

    repo = ExamRepository(db)
    return await repo.get_student_results(student.id)


@router.get("/assignments/", response_model=list[AssignmentResponse])
async def my_assignments(
    current_user: StudentAccess,
    db: AsyncSession = Depends(get_db),
) -> list[AssignmentResponse]:
    """
    Return assignments relevant to the authenticated student's course.
    Submissions from this student are embedded for status display.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.student import Student
    from app.models.assignment import Assignment

    result = await db.execute(select(Student).where(Student.user_id == current_user["sub"]))
    student = result.scalar_one_or_none()
    if not student:
        raise NotFoundError("Student profile", current_user["sub"])

    assignments = await db.execute(
        select(Assignment)
        .options(selectinload(Assignment.topics))
        .where(Assignment.target_course == student.course)
    )
    return assignments.scalars().all()


@router.post("/assignments/{assignment_id}/submit/", status_code=201)
async def submit_assignment(
    assignment_id: str,
    current_user: StudentAccess,
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
):
    """Upload an assignment submission file."""
    from sqlalchemy import select
    from app.models.student import Student
    from app.services.file_service import FileService

    result = await db.execute(select(Student).where(Student.user_id == current_user["sub"]))
    student = result.scalar_one_or_none()
    if not student:
        raise NotFoundError("Student profile", current_user["sub"])

    file_url = await FileService().save(file, subfolder="submissions")
    repo = AssignmentRepository(db)
    return await repo.submit(assignment_id, student.id, file_url)


@router.get("/materials")
async def my_materials(
    current_user: StudentAccess,
    db: AsyncSession = Depends(get_db),
) -> list:
    """Return all study materials for the student's department (flattened)."""
    from sqlalchemy import select
    from app.models.student import Student
    from app.models.subject import Subject

    # Find student/dept
    res = await db.execute(select(Student).where(Student.user_id == current_user["sub"]))
    student = res.scalar_one_or_none()
    if not student:
        raise NotFoundError("Student", current_user["sub"])

    # Find department subjects
    subj_res = await db.execute(select(Subject).where(Subject.department_id == student.department_id))
    subject_ids = [s.id for s in subj_res.scalars().all()]

    repo = MaterialRepository(db)
    return await repo.list_all_for_subjects(subject_ids)


@router.get("/materials/{subject_id}/")
async def study_materials(
    subject_id: str,
    _: StudentAccess,
    db: AsyncSession = Depends(get_db),
) -> list:
    """Return study material categories and files for a subject."""
    repo = MaterialRepository(db)
    return await repo.list_categories(subject_id)


@router.get("/timetable/{department_id}/", response_model=list[TimetableResponse])
async def timetable(
    department_id: str,
    _: StudentAccess,
    db: AsyncSession = Depends(get_db),
) -> list[TimetableResponse]:
    """Return the weekly timetable for a department."""
    from sqlalchemy import select
    from app.models.timetable import Timetable

    result = await db.execute(
        select(Timetable).where(Timetable.department_id == department_id)
    )
    return result.scalars().all()


@router.get("/timetable/", response_model=list[TimetableResponse])
async def my_timetable(
    current_user: StudentAccess,
    db: AsyncSession = Depends(get_db),
) -> list:
    """
    Return the weekly timetable for the authenticated student's department.
    Derives department_id from the student's profile so the caller does not
    need to know it.
    """
    from sqlalchemy import select
    from app.models.student import Student
    from app.models.timetable import Timetable
    from sqlalchemy.orm import selectinload

    result = await db.execute(select(Student).where(Student.user_id == current_user["sub"]))
    student = result.scalar_one_or_none()
    if not student:
        raise NotFoundError("Student profile", current_user["sub"])

    slots = await db.execute(
        select(Timetable)
        .options(selectinload(Timetable.subject))
        .where(Timetable.department_id == student.department_id)
    )
    raw = slots.scalars().all()

    return [
        {
            "id": s.id,
            "subject_id": s.subject_id,
            "subject_name": s.subject.name if s.subject else None,
            "subject_code": s.subject.code if s.subject else None,
            "department_id": s.department_id,
            "day_of_week": s.day_of_week,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "room": s.room,
        }
        for s in raw
    ]


@router.get("/exams/")
async def my_exams(
    current_user: StudentAccess,
    db: AsyncSession = Depends(get_db),
) -> list:
    """
    Return upcoming exams for the authenticated student's department,
    enriched with subject name.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.student import Student
    from app.models.exam import Exam

    result = await db.execute(select(Student).where(Student.user_id == current_user["sub"]))
    student = result.scalar_one_or_none()
    if not student:
        raise NotFoundError("Student profile", current_user["sub"])

    exams_res = await db.execute(
        select(Exam)
        .options(selectinload(Exam.subject))
        .where(Exam.department_id == student.department_id)
        .order_by(Exam.exam_date)
    )
    exams = exams_res.scalars().all()

    return [
        {
            "id": e.id,
            "name": e.name,
            "subject_id": e.subject_id,
            "subject_name": e.subject.name if e.subject else None,
            "department_id": e.department_id,
            "exam_date": e.exam_date,
            "exam_time": e.exam_time,
            "location": e.location,
            "max_marks": e.max_marks,
            "passing_marks": e.passing_marks,
        }
        for e in exams
    ]


@router.get("/materials/")
async def my_materials(
    current_user: StudentAccess,
    db: AsyncSession = Depends(get_db),
) -> list[MaterialCategoryResponse]:
    """
    Return all study materials for subjects taught in the student's department.
    Returns categories which contain the nested files.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.student import Student
    from app.models.subject import Subject
    from app.models.material import MaterialCategory

    result = await db.execute(select(Student).where(Student.user_id == current_user["sub"]))
    student = result.scalar_one_or_none()
    if not student:
        raise NotFoundError("Student profile", current_user["sub"])

    # Fetch all subjects for this department
    subjects_res = await db.execute(
        select(Subject).where(Subject.department_id == student.department_id)
    )
    subjects = subjects_res.scalars().all()
    subject_ids = [s.id for s in subjects]

    if not subject_ids:
        return []

    # Fetch categories with their materials for all relevant subjects
    categories_res = await db.execute(
        select(MaterialCategory)
        .options(selectinload(MaterialCategory.materials), selectinload(MaterialCategory.subject))
        .where(MaterialCategory.subject_id.in_(subject_ids))
        .order_by(MaterialCategory.date_created.desc())
    )
    categories = categories_res.scalars().all()
    
    # Flatten the response: Return a list of all materials across all categories
    flattened_materials = []
    for cat in categories:
        for mat in cat.materials:
            flattened_materials.append({
                "id": mat.id,
                "title": mat.file_name,
                "file_url": mat.file_url,
                "category": cat.name,
                "subject_name": cat.subject.name if cat.subject else "Unknown",
                "subject_code": cat.subject.code if cat.subject else "General",
                "date_added": mat.date_added,
                "created_at": mat.date_added.isoformat() if mat.date_added else None
            })
            
    return flattened_materials

@router.get('/events', response_model=list[EventResponse])
async def get_student_events(
    current_user: StudentAccess,
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select, or_
    from app.models.student import Student
    from app.models.event import Event

    # We fetch events where department_id is NULL (college-wide) 
    # OR department_id matches the student's department
    filters = [Event.department_id == None]
    
    student_res = await db.execute(select(Student).where(Student.user_id == current_user["sub"]))
    student = student_res.scalars().first()
    if student and student.department_id:
        filters.append(Event.department_id == student.department_id)

    stmt = select(Event).where(or_(*filters)).order_by(Event.event_date.asc())
    events_res = await db.execute(stmt)
    return events_res.scalars().all()

