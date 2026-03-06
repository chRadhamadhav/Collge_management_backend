"""
Auth routes — login and token refresh. Public endpoints, no auth required.
"""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.user import UserResponse, UserUpdate
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.services.file_service import FileService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Authenticate with email + password and receive JWT access and refresh tokens."""
    service = AuthService(UserRepository(db))
    return await service.login(data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Exchange a valid refresh token for a new access token."""
    service = AuthService(UserRepository(db))
    return await service.refresh(data)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Get the profile details of the currently authenticated user."""
    repo = UserRepository(db)
    user = await repo.get_by_id(current_user["sub"])
    if not user:
        raise NotFoundError("User", current_user["sub"])
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Update profile details of the currently authenticated user."""
    repo = UserRepository(db)
    user = await repo.get_by_id(current_user["sub"])
    if not user:
        raise NotFoundError("User", current_user["sub"])
    
    # We update the attributes explicitly instead of overwriting the role/admin statuses
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.avatar_url is not None:
        user.avatar_url = data.avatar_url
    if data.education is not None:
        user.education = data.education
    if data.dob is not None:
        user.dob = data.dob
    if data.phone is not None:
        user.phone = data.phone
    if data.info is not None:
        user.info = data.info
        
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Upload and set the profile picture for the currently authenticated user."""
    repo = UserRepository(db)
    user = await repo.get_by_id(current_user["sub"])
    if not user:
        raise NotFoundError("User", current_user["sub"])

    # Provide a subfolder like 'avatars'
    file_service = FileService()
    file_url = await file_service.save(file, subfolder="avatars")

    user.avatar_url = file_url
    await db.commit()
    await db.refresh(user)

    return user


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Log out the current user. 
    In a stateless JWT setup, true invalidation happens client-side by dropping the token.
    This endpoint exists to allow future token blocklisting or session tracking.
    """
    # If a TokenBlocklist table existed, we would add `current_user["jti"]` or token here.
    return {"success": True, "message": "Successfully logged out."}
