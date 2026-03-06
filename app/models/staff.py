"""
Staff model — role-specific profile for users with role=staff or role=hod.
"""
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class Staff(Base, TimestampMixin):
    __tablename__ = "staff"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    department_id: Mapped[str] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )
    designation: Mapped[str] = mapped_column(String(255), nullable=False, default="Lecturer")

    # Relationships
    user: Mapped["User"] = relationship(back_populates="staff_profile")  # noqa: F821
    department: Mapped["Department"] = relationship(back_populates="staff_members")  # noqa: F821
    subjects: Mapped[list["Subject"]] = relationship(back_populates="staff")  # noqa: F821
