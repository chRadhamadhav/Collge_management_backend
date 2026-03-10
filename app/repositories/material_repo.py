"""
Material repository — queries for material categories and course files.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.material import CourseMaterial, MaterialCategory
from app.schemas.material import MaterialCategoryCreate


class MaterialRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_category(self, data: MaterialCategoryCreate) -> MaterialCategory:
        # Check for existing category with same name (case-insensitive) for this subject
        stmt = select(MaterialCategory).where(
            MaterialCategory.subject_id == data.subject_id,
            MaterialCategory.name.ilike(data.name.strip())
        )
        result = await self._db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Load materials for existing one to be consistent with return type
            stmt_load = (
                select(MaterialCategory)
                .options(selectinload(MaterialCategory.materials))
                .where(MaterialCategory.id == existing.id)
            )
            result_load = await self._db.execute(stmt_load)
            return result_load.scalar_one()

        category = MaterialCategory(**data.model_dump())
        self._db.add(category)
        await self._db.commit()
        
        # Fetch with selectinload to avoid "MissingGreenlet" errors in the response schema
        stmt = (
            select(MaterialCategory)
            .options(selectinload(MaterialCategory.materials))
            .where(MaterialCategory.id == category.id)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def list_categories(self, subject_id: str) -> list[MaterialCategory]:
        print(f"[DEBUG] Listing categories for subject_id: {subject_id}")
        result = await self._db.execute(
            select(MaterialCategory)
            .options(selectinload(MaterialCategory.materials))
            .where(MaterialCategory.subject_id == subject_id)
        )
        cats = result.scalars().all()
        print(f"[DEBUG] Found {len(cats)} categories")
        return cats

    async def add_file(self, category_id: str, file_name: str, file_url: str) -> CourseMaterial:
        material = CourseMaterial(
            category_id=category_id,
            file_name=file_name,
            file_url=file_url,
        )
        self._db.add(material)
        await self._db.commit()
        await self._db.refresh(material)
        return material

    async def get_file_by_id(self, material_id: str) -> CourseMaterial | None:
        result = await self._db.execute(
            select(CourseMaterial).where(CourseMaterial.id == material_id)
        )
        return result.scalar_one_or_none()

    async def delete_file(self, material: CourseMaterial) -> None:
        await self._db.delete(material)
        await self._db.commit()

    async def list_all_for_subjects(self, subject_ids: list[str]) -> list[dict]:
        """Fetch all materials for a list of subjects, flattened with subject metadata."""
        from app.models.subject import Subject
        result = await self._db.execute(
            select(CourseMaterial, MaterialCategory.name.label("category_name"), Subject.name.label("subject_name"), Subject.code.label("subject_code"))
            .join(MaterialCategory, CourseMaterial.category_id == MaterialCategory.id)
            .join(Subject, MaterialCategory.subject_id == Subject.id)
            .where(Subject.id.in_(subject_ids))
            .order_by(CourseMaterial.date_added.desc())
        )
        
        items = []
        for row in result.all():
          material = row[0]
          items.append({
            "id": material.id,
            "title": material.file_name,
            "file_url": material.file_url,
            "category": row[1],
            "subject_name": row[2],
            "subject_code": row[3],
            "created_at": material.date_added.isoformat()
          })
        return items
