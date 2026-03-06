"""
Admin route tests — user CRUD, role filtering, deactivation.
"""
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def create_user(db_session, *, email: str, role: UserRole, full_name: str = "Test User") -> User:
    """Insert a User row directly — bypasses the API to isolate route tests."""
    user = User(
        email=email,
        hashed_password=hash_password("password123"),
        full_name=full_name,
        role=role,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def admin_token(user_id: str) -> str:
    return create_access_token(user_id, "admin")


def staff_token(user_id: str) -> str:
    return create_access_token(user_id, "staff")


# ─── GET /admin/users ─────────────────────────────────────────────────────────

class TestListUsers:
    @pytest.mark.asyncio
    async def test_returns_all_users(self, client: AsyncClient, db_session):
        """Admin can list all users in the system."""
        admin = await create_user(db_session, email="admin@test.com", role=UserRole.ADMIN)
        await create_user(db_session, email="staff1@test.com", role=UserRole.STAFF)
        await create_user(db_session, email="student1@test.com", role=UserRole.STUDENT)

        response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token(admin.id)}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3

    @pytest.mark.asyncio
    async def test_filter_by_role(self, client: AsyncClient, db_session):
        """Role filter returns only users matching that role."""
        admin = await create_user(db_session, email="admin@test.com", role=UserRole.ADMIN)
        await create_user(db_session, email="staff1@test.com", role=UserRole.STAFF)
        await create_user(db_session, email="staff2@test.com", role=UserRole.STAFF)
        await create_user(db_session, email="student1@test.com", role=UserRole.STUDENT)

        response = await client.get(
            "/api/v1/admin/users?role=staff",
            headers={"Authorization": f"Bearer {admin_token(admin.id)}"},
        )

        data = response.json()
        assert data["total"] == 2
        assert all(u["role"] == "staff" for u in data["users"])

    @pytest.mark.asyncio
    async def test_staff_cannot_list_users(self, client: AsyncClient, db_session):
        """Non-admin role must be rejected with 403."""
        staff = await create_user(db_session, email="staff@test.com", role=UserRole.STAFF)

        response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {staff_token(staff.id)}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_rejected(self, client: AsyncClient, db_session):
        """No token → 401."""
        response = await client.get("/api/v1/admin/users")
        assert response.status_code == 401


# ─── POST /admin/users ─────────────────────────────────────────────────────────

class TestCreateUser:
    @pytest.mark.asyncio
    async def test_create_staff_user(self, client: AsyncClient, db_session):
        """Admin can create a new staff account."""
        admin = await create_user(db_session, email="admin@test.com", role=UserRole.ADMIN)

        response = await client.post(
            "/api/v1/admin/users",
            json={
                "email": "newstaff@test.com",
                "password": "securepass1",
                "full_name": "New Staff",
                "role": "staff",
                "department_id": "dept-1",
                "designation": "Lecturer",
            },
            headers={"Authorization": f"Bearer {admin_token(admin.id)}"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "newstaff@test.com"
        assert body["role"] == "staff"

    @pytest.mark.asyncio
    async def test_create_student_user(self, client: AsyncClient, db_session):
        """Admin can create a student account with roll number and course."""
        admin = await create_user(db_session, email="admin@test.com", role=UserRole.ADMIN)

        response = await client.post(
            "/api/v1/admin/users",
            json={
                "email": "student@test.com",
                "password": "securepass1",
                "full_name": "New Student",
                "role": "student",
                "department_id": "dept-1",
                "roll_number": "CS001",
                "course": "CS",
                "semester": "3",
            },
            headers={"Authorization": f"Bearer {admin_token(admin.id)}"},
        )

        assert response.status_code == 201
        assert response.json()["role"] == "student"

    @pytest.mark.asyncio
    async def test_short_password_rejected(self, client: AsyncClient, db_session):
        """Password under 8 characters must fail Pydantic validation."""
        admin = await create_user(db_session, email="admin@test.com", role=UserRole.ADMIN)

        response = await client.post(
            "/api/v1/admin/users",
            json={
                "email": "user@test.com",
                "password": "short",
                "full_name": "Bad User",
                "role": "staff",
            },
            headers={"Authorization": f"Bearer {admin_token(admin.id)}"},
        )

        assert response.status_code == 422  # Pydantic validation error


# ─── PATCH /admin/users/{id}/deactivate ──────────────────────────────────────

class TestDeactivateUser:
    @pytest.mark.asyncio
    async def test_deactivate_existing_user(self, client: AsyncClient, db_session):
        """Admin can deactivate an active user — they cannot log in after."""
        admin = await create_user(db_session, email="admin@test.com", role=UserRole.ADMIN)
        target = await create_user(db_session, email="staff@test.com", role=UserRole.STAFF)

        response = await client.patch(
            f"/api/v1/admin/users/{target.id}/deactivate",
            headers={"Authorization": f"Bearer {admin_token(admin.id)}"},
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    @pytest.mark.asyncio
    async def test_deactivate_nonexistent_user(self, client: AsyncClient, db_session):
        """Deactivating an unknown user ID returns 404."""
        admin = await create_user(db_session, email="admin@test.com", role=UserRole.ADMIN)

        response = await client.patch(
            "/api/v1/admin/users/does-not-exist/deactivate",
            headers={"Authorization": f"Bearer {admin_token(admin.id)}"},
        )

        assert response.status_code == 404
        assert response.json()["error_code"] == "USER_NOT_FOUND"


# ─── DELETE /admin/users/{id} ─────────────────────────────────────────────────

class TestDeleteUser:
    @pytest.mark.asyncio
    async def test_delete_user(self, client: AsyncClient, db_session):
        """Admin can permanently delete a user — response is 204 no content."""
        admin = await create_user(db_session, email="admin@test.com", role=UserRole.ADMIN)
        target = await create_user(db_session, email="todelete@test.com", role=UserRole.STAFF)

        response = await client.delete(
            f"/api/v1/admin/users/{target.id}",
            headers={"Authorization": f"Bearer {admin_token(admin.id)}"},
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_404(self, client: AsyncClient, db_session):
        """Deleting a user that doesn't exist returns 404."""
        admin = await create_user(db_session, email="admin@test.com", role=UserRole.ADMIN)

        response = await client.delete(
            "/api/v1/admin/users/ghost-user-id",
            headers={"Authorization": f"Bearer {admin_token(admin.id)}"},
        )

        assert response.status_code == 404
