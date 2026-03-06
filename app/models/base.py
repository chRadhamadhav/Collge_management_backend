"""
SQLAlchemy declarative base and shared timestamp mixin.
All models inherit from Base and use UUIDs as primary keys.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Application-wide SQLAlchemy declarative base."""
    pass


class TimestampMixin:
    """
    Adds created_at and updated_at columns automatically managed by the database.
    Use this on any table that benefits from audit timestamps.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def new_uuid() -> str:
    """Generate a new UUID v4 string — used as primary key default."""
    return str(uuid.uuid4())
