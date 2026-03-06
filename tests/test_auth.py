"""
Auth endpoint integration tests.
"""
import pytest
from httpx import AsyncClient

from app.core.security import hash_password
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session):
    """A valid email/password should return access and refresh tokens."""
    # Arrange — create a user directly in the test DB
    user = User(
        email="admin@test.com",
        hashed_password=hash_password("password123"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.commit()

    # Act
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "password123"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db_session):
    """Wrong password must return 401 — not expose whether the email exists."""
    user = User(
        email="staff@test.com",
        hashed_password=hash_password("correct-password"),
        full_name="Test Staff",
        role=UserRole.STAFF,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "staff@test.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["error_code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient, db_session):
    """Non-existent email must return same 401 as wrong password (no user enumeration)."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@test.com", "password": "password123"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient, db_session):
    """Health endpoint must always return 200."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
