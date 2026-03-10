"""
User ORM model — the central identity table for all application roles.
A user row exists for every Admin, HOD, Staff, and Student.
Role-specific data lives in separate tables (Student, Staff) linked by user_id.
"""
import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    HOD = "hod"
    STAFF = "staff"
    STUDENT = "student"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    education: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dob: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    info: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Back-references populated by Student/Staff models
    student_profile: Mapped["Student"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )  # noqa: F821
    staff_profile: Mapped["Staff"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )  # noqa: F821
    announcements: Mapped[list["Announcement"]] = relationship(
        back_populates="created_by_user", cascade="all, delete-orphan"
    )  # noqa: F821
