"""
Announcement model — messages broadcast by HOD or Admin to a target role group.
"""
import enum

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class AnnouncementTarget(str, enum.Enum):
    ALL = "ALL"
    STUDENT = "STUDENT"
    STAFF = "STAFF"
    HOD = "HOD"


class Announcement(Base, TimestampMixin):
    __tablename__ = "announcements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Target audience — controls which role sees this announcement
    target_role: Mapped[AnnouncementTarget] = mapped_column(
        Enum(AnnouncementTarget), nullable=False, default=AnnouncementTarget.ALL
    )

    created_by_user: Mapped["User"] = relationship(back_populates="announcements")  # noqa: F821
