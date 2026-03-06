"""
Shared FastAPI dependencies.
- get_db: yields an async DB session
- get_current_user: validates JWT and returns the authenticated user
- require_role: factory that creates role-enforcing dependencies
"""
from typing import Annotated

from fastapi import Depends, Header
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.logger.logger import logger
from app.core.security import decode_token
from app.database import get_db


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Validate the Bearer token in the Authorization header.
    Returns the decoded token payload so downstream routes know user id and role.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Authorization header missing or malformed")

    token = authorization.removeprefix("Bearer ")

    try:
        payload = decode_token(token)
    except JWTError as exc:
        # Log token failures at debug level — not an error, just invalid/expired
        logger.debug("Token validation failed: {}", exc)
        raise UnauthorizedError("Token is invalid or expired") from exc

    if payload.get("type") != "access":
        raise UnauthorizedError("Refresh tokens cannot be used for API access")

    return payload


def require_role(*roles: str):
    """
    Dependency factory that restricts an endpoint to users with one of the given roles.
    Usage: Depends(require_role("admin", "hod"))
    """

    async def _check_role(
        current_user: Annotated[dict, Depends(get_current_user)],
    ) -> dict:
        if current_user.get("role") not in roles:
            raise ForbiddenError(
                f"This endpoint requires one of the following roles: {', '.join(roles)}"
            )
        return current_user

    return _check_role
