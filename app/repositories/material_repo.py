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
        category = MaterialCategory(**data.model_dump())
        self._db.add(category)
        await self._db.commit()
        await self._db.refresh(category)
        return category

    async def list_categories(self, subject_id: str) -> list[MaterialCategory]:
        result = await self._db.execute(
            select(MaterialCategory)
            .options(selectinload(MaterialCategory.materials))
            .where(MaterialCategory.subject_id == subject_id)
        )
        return result.scalars().all()

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
