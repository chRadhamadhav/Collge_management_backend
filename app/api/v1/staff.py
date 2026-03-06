"""
Staff routes — attendance, assignments, materials, exams, and marks.
Accessible by staff and hod roles.
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
from app.schemas.assignment import AssignmentCreate, AssignmentResponse, SubmissionGrade
from app.schemas.attendance import AttendanceBulkCreate
from app.schemas.exam import ExamCreate, ExamMarksBulkCreate, ExamResponse, ExamMarkResponse
from app.schemas.material import MaterialCategoryCreate, MaterialCategoryResponse, CourseMaterialResponse
from app.schemas.staff import StaffProfileResponse, StaffDashboardResponse
from app.schemas.subject import SubjectResponse
from app.schemas.student import StudentResponse
from app.services.file_service import FileService

router = APIRouter(prefix="/staff", tags=["staff"])

StaffAccess = Annotated[dict, Depends(require_role("staff", "hod", "admin"))]

# ─── Profile & Dashboard ──────────────────────────────────────────────────────

@router.get("/profile", response_model=StaffProfileResponse)
async def get_staff_profile(
    current_user: StaffAccess,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the profile details for the currently logged-in staff member."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.staff import Staff
    from app.models.user import User

    # We join Staff with User and Department
    result = await db.execute(
        select(Staff)
        .options(selectinload(Staff.user), selectinload(Staff.department))
        .where(Staff.user_id == current_user["sub"])
    )
    staff = result.scalar_one_or_none()
    
    if not staff:
        raise NotFoundError("Staff Profile", current_user["sub"])

    # Map SQL model to Response dict merging User/Staff/Dept fields
    return {
        "id": staff.id,
        "user_id": staff.user_id,
        "department_id": staff.department_id,
        "designation": staff.designation,
        "email": staff.user.email,
        "full_name": staff.user.full_name,
        "phone_number": staff.user.phone,
        "role": staff.user.role.value,
        "is_active": staff.user.is_active,
        "avatar_url": staff.user.avatar_url,
        "department_name": staff.department.name if staff.department else None,
    }


@router.get("/dashboard", response_model=StaffDashboardResponse)
async def get_staff_dashboard(
    current_user: StaffAccess,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get aggregate statistics for the dashboard of the logged-in staff member."""
    from sqlalchemy import select, func
    from app.models.staff import Staff
    from app.models.subject import Subject
    from app.models.student import Student
    from app.models.material import CourseMaterial
    from app.models.assignment import Assignment
    
    # 1. Get staff
    result = await db.execute(select(Staff).where(Staff.user_id == current_user["sub"]))
    staff = result.scalar_one_or_none()
    
    if not staff:
        raise NotFoundError("Staff Profile", current_user["sub"])
        
    # For now, MVP approach: Staff's subjects
    subjects_result = await db.execute(select(Subject).where(Subject.department_id == staff.department_id))
    subjects = subjects_result.scalars().all()
    subject_ids = [s.id for s in subjects]
    
    # Total Subjects
    total_subjects = len(subject_ids)
    
    # Total Students (in their department)
    total_students_res = await db.execute(
        select(func.count(Student.id)).where(Student.department_id == staff.department_id)
    )
    total_students = total_students_res.scalar_one_or_none() or 0
    
    # Total Materials
    # Assuming materials belong to the subjects in their department
    if total_subjects > 0:
        total_materials_res = await db.execute(
            select(func.count(CourseMaterial.id))
            .join(CourseMaterial.category)
            .where(CourseMaterial.category.has(subject_id=subject_ids[0])) # Simplified
        )
        total_materials = total_materials_res.scalar_one_or_none() or 0
        
        # Total Assignments
        total_assignments_res = await db.execute(
            select(func.count(Assignment.id))
            .where(Assignment.subject_id.in_(subject_ids))
        )
        total_assignments = total_assignments_res.scalar_one_or_none() or 0
    else:
        total_materials = 0
        total_assignments = 0

    return {
        "total_subjects": total_subjects,
        "total_students": total_students,
        "total_materials": total_materials,
        "total_assignments": total_assignments,
    }


# ─── Subjects & Students ──────────────────────────────────────────────────────

@router.get("/subjects", response_model=list[SubjectResponse])
async def list_subjects(
    current_user: StaffAccess,
    db: AsyncSession = Depends(get_db),
) -> list[SubjectResponse]:
    """List all subjects in the staff's department."""
    from sqlalchemy import select
    from app.models.staff import Staff
    from app.models.subject import Subject
    
    result = await db.execute(select(Staff).where(Staff.user_id == current_user["sub"]))
    staff = result.scalar_one_or_none()
    if staff:
        subjects = await db.execute(select(Subject).where(Subject.department_id == staff.department_id))
        return subjects.scalars().all()
    
    subjects = await db.execute(select(Subject))
    return subjects.scalars().all()


@router.get("/subjects/{subject_id}/students", response_model=list[StudentResponse])
async def list_students_for_subject(
    subject_id: str,
    _: StaffAccess,
    db: AsyncSession = Depends(get_db),
) -> list[StudentResponse]:
    """List all students enrolled in a subject. (In this MVP, all students in the subject's department)."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.subject import Subject
    from app.models.student import Student
    
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise NotFoundError("Subject", subject_id)
        
    students = await db.execute(
        select(Student)
        .options(selectinload(Student.user))
        .where(Student.department_id == subject.department_id)
    )
    return students.scalars().all()


# ─── Attendance ───────────────────────────────────────────────────────────────

@router.post("/attendance", status_code=204)
async def submit_attendance(
    data: AttendanceBulkCreate,
    _: StaffAccess,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Submit or update attendance for an entire class on a given date."""
    repo = AttendanceRepository(db)
    await repo.bulk_upsert(data)


# ─── Materials ────────────────────────────────────────────────────────────────

@router.post("/materials/categories", response_model=MaterialCategoryResponse, status_code=201)
async def create_category(
    data: MaterialCategoryCreate,
    _: StaffAccess,
    db: AsyncSession = Depends(get_db),
) -> MaterialCategoryResponse:
    """Create a material category (e.g., 'Lecture Notes') under a subject."""
    repo = MaterialRepository(db)
    return await repo.create_category(data)


@router.get("/materials/{subject_id}", response_model=list[MaterialCategoryResponse])
async def list_materials(
    subject_id: str,
    _: StaffAccess,
    db: AsyncSession = Depends(get_db),
) -> list[MaterialCategoryResponse]:
    """List all material categories (with their files) for a subject."""
    repo = MaterialRepository(db)
    return await repo.list_categories(subject_id)


@router.post("/materials/{category_id}/upload", response_model=CourseMaterialResponse, status_code=201)
async def upload_material(
    category_id: str,
    _: StaffAccess,
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
) -> CourseMaterialResponse:
    """Upload a study material file into a category."""
    file_url = await FileService().save(file, subfolder="materials")
    repo = MaterialRepository(db)
    return await repo.add_file(category_id, file.filename or "file", file_url)


@router.delete("/materials/{material_id}", status_code=204)
async def delete_material(
    material_id: str,
    _: StaffAccess,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a material file from a category."""
    repo = MaterialRepository(db)
    material = await repo.get_file_by_id(material_id)
    if not material:
        raise NotFoundError("Material", material_id)
    await FileService().delete(material.file_url)
    await repo.delete_file(material)


# ─── Assignments ──────────────────────────────────────────────────────────────

@router.post("/assignments", response_model=AssignmentResponse, status_code=201)
async def create_assignment(
    data: AssignmentCreate,
    current_user: StaffAccess,
    db: AsyncSession = Depends(get_db),
) -> AssignmentResponse:
    """Create an assignment with topics for a course."""
    repo = AssignmentRepository(db)
    return await repo.create(data, created_by_id=current_user["sub"])


@router.get("/assignments/{subject_id}", response_model=list[AssignmentResponse])
async def list_assignments(
    subject_id: str,
    _: StaffAccess,
    db: AsyncSession = Depends(get_db),
) -> list[AssignmentResponse]:
    """List all assignments for a subject."""
    repo = AssignmentRepository(db)
    return await repo.list_by_subject(subject_id)


@router.delete("/assignments/{assignment_id}", status_code=204)
async def delete_assignment(
    assignment_id: str,
    _: StaffAccess,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an assignment and all its topics and submissions."""
    repo = AssignmentRepository(db)
    assignment = await repo.get_by_id(assignment_id)
    if not assignment:
        raise NotFoundError("Assignment", assignment_id)
    await repo.delete(assignment)


@router.get("/assignments/{assignment_id}/submissions")
async def get_submissions(
    assignment_id: str,
    _: StaffAccess,
    db: AsyncSession = Depends(get_db),
) -> list:
    """Retrieve all student submissions for an assignment."""
    repo = AssignmentRepository(db)
    return await repo.get_submissions(assignment_id)


@router.put("/submissions/{submission_id}/grade", status_code=200)
async def grade_submission(
    submission_id: str,
    data: SubmissionGrade,
    _: StaffAccess,
    db: AsyncSession = Depends(get_db),
):
    """Assign marks to a student's submission."""
    repo = AssignmentRepository(db)
    result = await repo.grade_submission(submission_id, data.marks_given)
    if not result:
        raise NotFoundError("Submission", submission_id)
    return result


# ─── Exams ────────────────────────────────────────────────────────────────────

@router.post("/exams", response_model=ExamResponse, status_code=201)
async def create_exam(
    data: ExamCreate,
    _: StaffAccess,
    db: AsyncSession = Depends(get_db),
) -> ExamResponse:
    """Create an exam for a subject."""
    repo = ExamRepository(db)
    return await repo.create_exam(data)


@router.get("/exams", response_model=list[ExamResponse])
async def list_exams(
    current_user: StaffAccess,
    db: AsyncSession = Depends(get_db),
) -> list[ExamResponse]:
    """List exams for the staff's department."""
    from sqlalchemy import select
    from app.models.staff import Staff
    from app.models.exam import Exam
    
    result = await db.execute(select(Staff).where(Staff.user_id == current_user["sub"]))
    staff = result.scalar_one_or_none()
    
    if staff:
        exams = await db.execute(select(Exam).where(Exam.department_id == staff.department_id))
        return exams.scalars().all()
    
    # Fallback to all exams if no specific staff profile found (e.g. admin testing)
    exams = await db.execute(select(Exam))
    return exams.scalars().all()


@router.get("/exams/{exam_id}/marks", response_model=list[ExamMarkResponse])
async def get_exam_marks(
    exam_id: str,
    _: StaffAccess,
    db: AsyncSession = Depends(get_db),
) -> list[ExamMarkResponse]:
    """Get all marks for an exam."""
    repo = ExamRepository(db)
    return await repo.get_exam_marks(exam_id)


@router.post("/exams/{exam_id}/marks", status_code=204)
async def enter_marks(
    exam_id: str,
    data: ExamMarksBulkCreate,
    _: StaffAccess,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Enter or update marks for all students in an exam."""
    repo = ExamRepository(db)
    await repo.bulk_save_marks(data)


@router.delete("/exams/{exam_id}", status_code=204)
async def delete_exam(
    exam_id: str,
    _: StaffAccess,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an exam."""
    from sqlalchemy import select
    from app.models.exam import Exam
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise NotFoundError("Exam", exam_id)
    await db.delete(exam)
    await db.commit()
