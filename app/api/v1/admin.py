"""
Admin routes — user management and system statistics.
Restricted to users with role=admin.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, UploadFile, File
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


@router.post("/users/bulk", status_code=201)
async def bulk_create_users(
    _: AdminOnly,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Bulk create users from an uploaded Excel file."""
    import pandas as pd
    import io
    from app.schemas.user import UserCreate

    content = await file.read()
    try:
        df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Invalid Excel file: {str(e)}")

    repo = UserRepository(db)
    created_count = 0
    errors = []

    for index, row in df.iterrows():
        try:
            # Normalize role to lowercase to match UserRole enum
            role_val = str(row.get("role", "student")).lower()
            
            # Basic validation of required fields in row
            if not row.get("email") or not row.get("full_name"):
                errors.append({"row": index + 2, "error": "Missing email or full_name"})
                continue

            # Check if user already exists
            existing = await repo.get_by_email(row["email"])
            if existing:
                errors.append({"row": index + 2, "error": f"User with email {row['email']} already exists"})
                continue

            user_data = {
                "email": row["email"],
                "password": str(row.get("password", "college123")),
                "full_name": row["full_name"],
                "role": role_val,
                "department": row.get("department"),
                "roll_number": str(row.get("roll_number", "")) if pd.notnull(row.get("roll_number")) else None,
                "course": row.get("course"),
                "semester": str(row.get("semester", "")) if pd.notnull(row.get("semester")) else None,
                "designation": row.get("designation"),
            }

            # Remove None values so Pydantic uses defaults or keeps them optional
            user_data = {k: v for k, v in user_data.items() if v is not None}
            
            user_create = UserCreate(**user_data)
            await repo.create(user_create)
            created_count += 1
        except Exception as e:
            errors.append({"row": index + 2, "error": str(e)})

    return {
        "success": True,
        "message": f"Successfully created {created_count} users",
        "created_count": created_count,
        "errors": errors
    }
