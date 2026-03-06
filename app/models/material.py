"""
MaterialCategory and CourseMaterial models.
Maps to Flutter's MaterialCategory and CourseMaterial Hive models.
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid


class MaterialCategory(Base):
    """A named grouping of study materials within a subject (e.g., 'Lecture Notes', 'Lab Manuals')."""
    __tablename__ = "material_categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_id: Mapped[str] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    date_created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    subject: Mapped["Subject"] = relationship(back_populates="material_categories")  # noqa: F821
    materials: Mapped[list["CourseMaterial"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class CourseMaterial(Base):
    """A single file (PDF, doc, etc.) uploaded by staff under a material category."""
    __tablename__ = "course_materials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    category_id: Mapped[str] = mapped_column(
        ForeignKey("material_categories.id", ondelete="CASCADE"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # The stored file path or cloud storage URL — abstract behind FileService
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    date_added: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    category: Mapped["MaterialCategory"] = relationship(back_populates="materials")
