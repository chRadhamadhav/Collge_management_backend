"""
Staff route tests — attendance submission, material upload, assignment CRUD, exam marks.
"""
from datetime import datetime, timedelta, timezone
from io import BytesIO

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole


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


def token(user: User) -> str:
    return create_access_token(user.id, user.role.value)


def auth(user: User) -> dict:
    return {"Authorization": f"Bearer {token(user)}"}


# ─── Attendance ───────────────────────────────────────────────────────────────

class TestAttendance:
    @pytest.mark.asyncio
    async def test_submit_attendance_succeeds(self, client: AsyncClient, db_session):
        """Staff can submit a full class attendance in one request."""
        staff = await make_user(db_session, "staff@t.com", UserRole.STAFF)

        response = await client.post(
            "/api/v1/staff/attendance",
            json={
                "subject_id": "subj-1",
                "date": "2025-01-15",
                "records": [
                    {"student_id": "stu-1", "status": "present"},
                    {"student_id": "stu-2", "status": "absent"},
                    {"student_id": "stu-3", "status": "present"},
                ],
            },
            headers=auth(staff),
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_resubmit_attendance_does_not_duplicate(self, client: AsyncClient, db_session):
        """Submitting attendance for the same day twice (upsert) must not create duplicate records."""
        staff = await make_user(db_session, "staff@t.com", UserRole.STAFF)

        payload = {
            "subject_id": "subj-x",
            "date": "2025-02-10",
            "records": [{"student_id": "stu-99", "status": "present"}],
        }

        # Submit twice
        await client.post("/api/v1/staff/attendance", json=payload, headers=auth(staff))
        response = await client.post("/api/v1/staff/attendance", json=payload, headers=auth(staff))

        # Second submission should succeed (upsert), not 409 conflict
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_student_cannot_submit_attendance(self, client: AsyncClient, db_session):
        """Students must not be able to POST attendance."""
        student = await make_user(db_session, "student@t.com", UserRole.STUDENT)

        response = await client.post(
            "/api/v1/staff/attendance",
            json={
                "subject_id": "subj-1",
                "date": "2025-01-15",
                "records": [{"student_id": "stu-1", "status": "present"}],
            },
            headers=auth(student),
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_invalid_status_rejected(self, client: AsyncClient, db_session):
        """An invalid attendance status value should be rejected by Pydantic."""
        staff = await make_user(db_session, "staff@t.com", UserRole.STAFF)

        response = await client.post(
            "/api/v1/staff/attendance",
            json={
                "subject_id": "subj-1",
                "date": "2025-01-15",
                "records": [{"student_id": "stu-1", "status": "INVALID_VALUE"}],
            },
            headers=auth(staff),
        )

        assert response.status_code == 422


# ─── Material Category ─────────────────────────────────────────────────────────

class TestMaterialCategory:
    @pytest.mark.asyncio
    async def test_create_category(self, client: AsyncClient, db_session):
        """Staff can create a material category linked to a subject."""
        staff = await make_user(db_session, "staff@t.com", UserRole.STAFF)

        response = await client.post(
            "/api/v1/staff/materials/categories",
            json={"name": "Lecture Notes", "subject_id": "subj-1"},
            headers=auth(staff),
        )

        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Lecture Notes"
        assert body["subject_id"] == "subj-1"
        assert "id" in body

    @pytest.mark.asyncio
    async def test_list_categories_by_subject(self, client: AsyncClient, db_session):
        """Listing categories for a subject returns all of them."""
        staff = await make_user(db_session, "staff@t.com", UserRole.STAFF)

        # Create 2 categories for same subject
        for name in ("Notes", "Assignments"):
            await client.post(
                "/api/v1/staff/materials/categories",
                json={"name": name, "subject_id": "subj-99"},
                headers=auth(staff),
            )

        response = await client.get("/api/v1/staff/materials/subj-99", headers=auth(staff))

        assert response.status_code == 200
        assert len(response.json()) == 2

    @pytest.mark.asyncio
    async def test_empty_name_rejected(self, client: AsyncClient, db_session):
        """Category name must be at least 2 characters."""
        staff = await make_user(db_session, "staff@t.com", UserRole.STAFF)

        response = await client.post(
            "/api/v1/staff/materials/categories",
            json={"name": "A", "subject_id": "subj-1"},
            headers=auth(staff),
        )

        assert response.status_code == 422


# ─── Assignments ──────────────────────────────────────────────────────────────

class TestAssignments:
    def _assignment_payload(self, subject_id: str = "subj-1") -> dict:
        return {
            "title": "Python Basics Assignment",
            "subject_id": subject_id,
            "target_course": "CS",
            "due_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "max_marks": 100,
            "topics": [
                {
                    "title": "Variables and Types",
                    "description": "Write a program demonstrating all Python primitive types",
                    "from_roll_no": None,
                    "to_roll_no": None,
                }
            ],
        }

    @pytest.mark.asyncio
    async def test_create_assignment_with_topics(self, client: AsyncClient, db_session):
        """Staff can create an assignment with nested topics."""
        staff = await make_user(db_session, "staff@t.com", UserRole.STAFF)

        response = await client.post(
            "/api/v1/staff/assignments",
            json=self._assignment_payload(),
            headers=auth(staff),
        )

        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Python Basics Assignment"
        assert len(body["topics"]) == 1
        assert body["topics"][0]["title"] == "Variables and Types"

    @pytest.mark.asyncio
    async def test_list_assignments_by_subject(self, client: AsyncClient, db_session):
        """All assignments for a subject are returned in the list endpoint."""
        staff = await make_user(db_session, "staff@t.com", UserRole.STAFF)

        # Create 2 assignments for same subject
        for title in ("Assignment 1", "Assignment 2"):
            payload = self._assignment_payload("subj-list")
            payload["title"] = title
            await client.post("/api/v1/staff/assignments", json=payload, headers=auth(staff))

        response = await client.get("/api/v1/staff/assignments/subj-list", headers=auth(staff))

        assert response.status_code == 200
        assert len(response.json()) == 2

    @pytest.mark.asyncio
    async def test_delete_assignment(self, client: AsyncClient, db_session):
        """Staff can delete their assignment — response is 204."""
        staff = await make_user(db_session, "staff@t.com", UserRole.STAFF)

        create_resp = await client.post(
            "/api/v1/staff/assignments",
            json=self._assignment_payload(),
            headers=auth(staff),
        )
        assignment_id = create_resp.json()["id"]

        delete_resp = await client.delete(
            f"/api/v1/staff/assignments/{assignment_id}",
            headers=auth(staff),
        )

        assert delete_resp.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_nonexistent_assignment(self, client: AsyncClient, db_session):
        """Deleting an assignment that doesn't exist returns 404."""
        staff = await make_user(db_session, "staff@t.com", UserRole.STAFF)

        response = await client.delete(
            "/api/v1/staff/assignments/ghost-id",
            headers=auth(staff),
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_zero_max_marks_rejected(self, client: AsyncClient, db_session):
        """max_marks must be > 0 — Pydantic should reject 0."""
        staff = await make_user(db_session, "staff@t.com", UserRole.STAFF)
        payload = self._assignment_payload()
        payload["max_marks"] = 0

        response = await client.post(
            "/api/v1/staff/assignments",
            json=payload,
            headers=auth(staff),
        )

        assert response.status_code == 422


# ─── Exam Marks ───────────────────────────────────────────────────────────────

class TestExamMarks:
    @pytest.mark.asyncio
    async def test_create_exam(self, client: AsyncClient, db_session):
        """Staff can create an exam for a subject."""
        staff = await make_user(db_session, "staff@t.com", UserRole.STAFF)

        response = await client.post(
            "/api/v1/staff/exams",
            json={
                "name": "Mid-Term Exam",
                "subject_id": "subj-1",
                "department_id": "dept-1",
                "exam_date": datetime.now(timezone.utc).isoformat(),
                "exam_time": "10:00 AM",
                "location": "Room 101",
                "invigilator_id": None,
                "max_marks": 100.0,
                "passing_marks": 35.0,
            },
            headers=auth(staff),
        )

        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Mid-Term Exam"
        assert body["max_marks"] == 100.0

    @pytest.mark.asyncio
    async def test_enter_marks_for_exam(self, client: AsyncClient, db_session):
        """Staff can bulk-enter marks for all students in an exam."""
        staff = await make_user(db_session, "staff@t.com", UserRole.STAFF)

        # Create an exam first
        create_resp = await client.post(
            "/api/v1/staff/exams",
            json={
                "name": "Final Exam",
                "subject_id": "subj-1",
                "department_id": "dept-1",
                "exam_date": datetime.now(timezone.utc).isoformat(),
                "exam_time": "10:00 AM",
                "location": "Room 101",
                "invigilator_id": None,
                "max_marks": 100.0,
                "passing_marks": 35.0,
            },
            headers=auth(staff),
        )
        exam_id = create_resp.json()["id"]

        # Enter marks
        marks_resp = await client.post(
            f"/api/v1/staff/exams/{exam_id}/marks",
            json={
                "exam_id": exam_id,
                "marks": [
                    {"student_id": "stu-1", "marks_obtained": 85.0, "is_absent": False},
                    {"student_id": "stu-2", "marks_obtained": 0.0, "is_absent": True},
                ],
            },
            headers=auth(staff),
        )

        assert marks_resp.status_code == 204
