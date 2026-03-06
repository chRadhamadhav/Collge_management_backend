"""
JWT creation/verification and password hashing.
All cryptographic operations in the application live here.
"""
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if `plain` matches the stored `hashed` password."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

def _create_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    """Internal: sign a JWT with the configured secret and expiry."""
    payload = data | {"exp": datetime.now(UTC) + expires_delta}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(user_id: str, role: str) -> str:
    """Create a short-lived access token carrying user identity and role."""
    return _create_token(
        {"sub": user_id, "role": role, "type": "access"},
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: str) -> str:
    """Create a long-lived refresh token for obtaining new access tokens."""
    return _create_token(
        {"sub": user_id, "type": "refresh"},
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT.
    Raises JWTError if the token is invalid or expired — callers must handle this.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
