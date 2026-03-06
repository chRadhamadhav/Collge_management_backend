"""
Admin routes — user management and system statistics.
Restricted to users with role=admin.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role
from app.models.user import UserRole
from app.repositories.user_repo import UserRepository
from app.repositories.admin_repo import AdminRepository
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.schemas.admin import AdminDashboardStats

router = APIRouter(prefix="/admin", tags=["admin"])

AdminOnly = Annotated[dict, Depends(require_role("admin"))]


@router.get("/statistics", response_model=AdminDashboardStats)
async def get_dashboard_statistics(
    _: AdminOnly,
    db: AsyncSession = Depends(get_db),
) -> AdminDashboardStats:
    """Get aggregated statistics for the admin dashboard."""
    repo = AdminRepository(db)
    return await repo.get_dashboard_stats()


@router.get("/users", response_model=UserListResponse)
async def list_users(
    _: AdminOnly,
    db: AsyncSession = Depends(get_db),
    role: UserRole | None = Query(default=None, description="Filter by role"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=200),
) -> UserListResponse:
    """List all users with optional role filter and pagination."""
    repo = UserRepository(db)
    users, total = await repo.list_by_role(role, skip=skip, limit=limit)
    return UserListResponse(users=users, total=total)


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    _: AdminOnly,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Create a new user account (student, staff, HOD, or admin)."""
    try:
        repo = UserRepository(db)
        user = await repo.create(data)
        return user
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e


@router.patch("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: str,
    _: AdminOnly,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Deactivate a user account without deleting their data."""
    from app.core.exceptions import NotFoundError
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise NotFoundError("User", user_id)
    return await repo.update_active(user, is_active=False)


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    _: AdminOnly,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Permanently delete a user and all their associated records (cascade)."""
    from app.core.exceptions import NotFoundError
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise NotFoundError("User", user_id)
    await repo.delete(user)
