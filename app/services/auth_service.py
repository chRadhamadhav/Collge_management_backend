"""
Auth service — business logic for login and token refresh.
Raises domain exceptions; never returns HTTP responses.
"""
from jose import JWTError

from app.core.exceptions import UnauthorizedError
from app.core.logger.logger import logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._repo = user_repo

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self._repo.get_by_email(data.email)

        # Use the same error message for wrong email and wrong password
        # to prevent user enumeration attacks
        if not user or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedError("Account is deactivated")

        logger.info("User {} logged in with role {}", user.id, user.role.value)

        return TokenResponse(
            access_token=create_access_token(user.id, user.role.value),
            refresh_token=create_refresh_token(user.id),
            role=user.role.value,
            user_id=user.id,
        )

    async def refresh(self, data: RefreshRequest) -> TokenResponse:
        try:
            payload = decode_token(data.refresh_token)
        except JWTError as exc:
            raise UnauthorizedError("Invalid or expired refresh token") from exc

        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")

        user = await self._repo.get_by_id(payload["sub"])
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or deactivated")

        return TokenResponse(
            access_token=create_access_token(user.id, user.role.value),
            refresh_token=create_refresh_token(user.id),
            role=user.role.value,
            user_id=user.id,
        )
