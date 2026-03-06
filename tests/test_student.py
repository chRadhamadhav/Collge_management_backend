"""
Student route tests — attendance summary, results, assignments list, timetable.
Tests that students only see their own data and cannot access restricted endpoints.
"""
from datetime import date, datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.attendance import Attendance, AttendanceStatus
from app.models.exam import Exam, ExamMark


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def make_user(db: AsyncSession, email: str, role: UserRole) -> User:
    user = User(
        email=email,
        hashed_password=hash_password("password123"),
        full_name="Test Person",
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def make_student(db: AsyncSession, user: User) -> Student:
    student = Student(
        user_id=user.id,
        roll_number="CS001",
        course="CS",
        semester="3",
        department_id="dept-1",
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student


def auth_header(user: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role.value)}"}


# ─── Attendance Summary ───────────────────────────────────────────────────────

class TestStudentAttendance:
    @pytest.mark.asyncio
    async def test_no_profile_returns_404(self, client: AsyncClient, db_session):
        """A user with student role but no student profile row returns 404."""
        user = await make_user(db_session, "orphan@test.com", UserRole.STUDENT)

        response = await client.get("/api/v1/student/attendance", headers=auth_header(user))

        assert response.status_code == 404
        assert response.json()["error_code"] == "STUDENT_PROFILE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_empty_attendance_returns_empty_list(self, client: AsyncClient, db_session):
        """Student with no attendance records gets an empty array, not an error."""
        user = await make_user(db_session, "student@test.com", UserRole.STUDENT)
        await make_student(db_session, user)

        response = await client.get("/api/v1/student/attendance", headers=auth_header(user))

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_attendance_percentage_calculated(self, client: AsyncClient, db_session):
        """Attendance summary includes correct percentage — not left to the client to compute."""
        user = await make_user(db_session, "student@test.com", UserRole.STUDENT)
        student = await make_student(db_session, user)

        # 3 present, 1 absent → 75%
        records = [
            Attendance(student_id=student.id, subject_id="subj-1", date=date(2025, 1, i + 1), status=AttendanceStatus.PRESENT)
            for i in range(3)
        ] + [
            Attendance(student_id=student.id, subject_id="subj-1", date=date(2025, 1, 10), status=AttendanceStatus.ABSENT)
        ]
        for r in records:
            db_session.add(r)
        await db_session.commit()

        response = await client.get("/api/v1/student/attendance", headers=auth_header(user))

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        subject_data = data[0]
        assert subject_data["total"] == 4
        assert subject_data["attended"] == 3
        assert subject_data["percentage"] == 75.0


# ─── Exam Results ─────────────────────────────────────────────────────────────

class TestStudentResults:
    @pytest.mark.asyncio
    async def test_no_profile_returns_404(self, client: AsyncClient, db_session):
        """Student user without a profile gets 404 on results."""
        user = await make_user(db_session, "orphan@test.com", UserRole.STUDENT)

        response = await client.get("/api/v1/student/results", headers=auth_header(user))

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_results_empty_when_no_exams(self, client: AsyncClient, db_session):
        """Student with no exam marks gets an empty array."""
        user = await make_user(db_session, "student@test.com", UserRole.STUDENT)
        await make_student(db_session, user)

        response = await client.get("/api/v1/student/results", headers=auth_header(user))

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_results_returned_with_marks(self, client: AsyncClient, db_session):
        """Student's exam marks are returned in the results list."""
        user = await make_user(db_session, "student@test.com", UserRole.STUDENT)
        student = await make_student(db_session, user)

        # Create an exam and a mark for this student
        exam = Exam(
            name="Final Exam",
            subject_id="subj-1",
            department_id="dept-1",
            max_marks=100.0,
            passing_marks=35.0,
        )
        db_session.add(exam)
        await db_session.flush()

        mark = ExamMark(
            exam_id=exam.id,
            student_id=student.id,
            marks_obtained=82.5,
            is_absent=False,
        )
        db_session.add(mark)
        await db_session.commit()

        response = await client.get("/api/v1/student/results", headers=auth_header(user))

        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["marks_obtained"] == 82.5
        assert results[0]["is_absent"] is False


# ─── Assignments (Student view) ───────────────────────────────────────────────

class TestStudentAssignments:
    @pytest.mark.asyncio
    async def test_no_profile_returns_404(self, client: AsyncClient, db_session):
        """Student without profile gets 404 on assignments."""
        user = await make_user(db_session, "orphan@test.com", UserRole.STUDENT)

        response = await client.get("/api/v1/student/assignments", headers=auth_header(user))

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_assignments_filtered_by_course(self, client: AsyncClient, db_session):
        """Student only sees assignments targeting their course."""
        from app.models.assignment import Assignment

        user = await make_user(db_session, "student@test.com", UserRole.STUDENT)
        await make_student(db_session, user)  # course = "CS"

        # Assignment for CS (should be visible)
        cs_assignment = Assignment(
            title="CS Assignment",
            subject_id="subj-1",
            target_course="CS",
            due_date=datetime.now(timezone.utc) + timedelta(days=3),
            max_marks=50,
        )
        # Assignment for IT (should NOT be visible)
        it_assignment = Assignment(
            title="IT Assignment",
            subject_id="subj-2",
            target_course="IT",
            due_date=datetime.now(timezone.utc) + timedelta(days=3),
            max_marks=50,
        )
        db_session.add_all([cs_assignment, it_assignment])
        await db_session.commit()

        response = await client.get("/api/v1/student/assignments", headers=auth_header(user))

        assert response.status_code == 200
        data = response.json()
        # Only CS assignment visible
        assert len(data) == 1
        assert data[0]["title"] == "CS Assignment"


# ─── Timetable (Student view) ─────────────────────────────────────────────────

class TestStudentTimetable:
    @pytest.mark.asyncio
    async def test_timetable_returns_slots(self, client: AsyncClient, db_session):
        """Student can view timetable slots for their department."""
        from app.models.timetable import Timetable, DayOfWeek
        from datetime import time

        user = await make_user(db_session, "student@test.com", UserRole.STUDENT)

        slot = Timetable(
            subject_id="subj-1",
            department_id="dept-1",
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(9, 0),
            end_time=time(10, 0),
            room="Room 101",
        )
        db_session.add(slot)
        await db_session.commit()

        response = await client.get(
            "/api/v1/student/timetable/dept-1",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["room"] == "Room 101"

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_view_timetable(self, client: AsyncClient, db_session):
        """No token → 401."""
        response = await client.get("/api/v1/student/timetable/dept-1")
        assert response.status_code == 401


# ─── Profile ──────────────────────────────────────────────────────────────────

class TestStudentProfile:
    @pytest.mark.asyncio
    async def test_get_student_profile_success(self, client: AsyncClient, db_session):
        user = await make_user(db_session, "profile@test.com", UserRole.STUDENT)
        from app.models.department import Department
        dept = Department(name="Computer Science")
        db_session.add(dept)
        await db_session.flush()

        student = Student(
            user_id=user.id,
            roll_number="CS-PROF",
            course="B.Tech",
            semester="4",
            department_id=dept.id,
        )
        db_session.add(student)
        await db_session.commit()

        response = await client.get("/api/v1/student/profile", headers=auth_header(user))

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "profile@test.com"
        assert data["roll_number"] == "CS-PROF"
        assert data["department_name"] == "Computer Science"

    @pytest.mark.asyncio
    async def test_get_student_profile_not_found(self, client: AsyncClient, db_session):
        user = await make_user(db_session, "noprofile@test.com", UserRole.STUDENT)
        
        response = await client.get("/api/v1/student/profile", headers=auth_header(user))
        
        assert response.status_code == 404

# ─── Dashboard ────────────────────────────────────────────────────────────────

class TestStudentDashboard:
    @pytest.mark.asyncio
    async def test_get_dashboard_stats(self, client: AsyncClient, db_session):
        user = await make_user(db_session, "dash@test.com", UserRole.STUDENT)
        from app.models.department import Department
        dept = Department(name="Computer Science")
        db_session.add(dept)
        await db_session.flush()

        student = Student(
            user_id=user.id,
            roll_number="CS-DASH",
            course="B.Tech",
            semester="4",
            department_id=dept.id,
        )
        db_session.add(student)
        await db_session.commit()

        # Just fetching the dashboard should succeed without crashing, even if 0 stats
        response = await client.get("/api/v1/student/dashboard", headers=auth_header(user))
        assert response.status_code == 200
        data = response.json()
        assert data["attendance_percentage"] == 0.0
        assert data["total_assignments"] == 0
        assert data["upcoming_exams"] == 0


# ─── Events ───────────────────────────────────────────────────────────────────

class TestStudentEvents:
    @pytest.mark.asyncio
    async def test_get_events(self, client: AsyncClient, db_session):
        user = await make_user(db_session, "events@test.com", UserRole.STUDENT)
        from app.models.department import Department
        from app.models.event import Event, EventType
        
        dept1 = Department(name="Computer Science")
        dept2 = Department(name="Mechanical")
        db_session.add_all([dept1, dept2])
        await db_session.flush()

        student = Student(
            user_id=user.id,
            roll_number="CS-EVT",
            course="B.Tech",
            semester="4",
            department_id=dept1.id,
        )
        db_session.add(student)
        
        # Add a global event
        evt_global = Event(title="Global Event", event_date=date(2025,1,1), event_type=EventType.HOLIDAY, department_id=None)
        # Add a dept1 event
        evt_cs = Event(title="CS Event", event_date=date(2025,1,2), event_type=EventType.ACADEMIC, department_id=dept1.id)
        # Add a dept2 event
        evt_me = Event(title="ME Event", event_date=date(2025,1,3), event_type=EventType.ACADEMIC, department_id=dept2.id)
        
        db_session.add_all([evt_global, evt_cs, evt_me])
        await db_session.commit()

        response = await client.get("/api/v1/student/events", headers=auth_header(user))
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Should see global + cs, but not me
        titles = [e["title"] for e in data]
        assert "Global Event" in titles
        assert "CS Event" in titles
        assert "ME Event" not in titles

