"""
User repository — all SQL queries for the users, students, and staff tables.
Services call this; routes never touch the DB directly.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.models.student import Student
from app.models.staff import Staff
from app.models.user import User, UserRole
from app.models.department import Department
from app.schemas.user import UserCreate


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self._db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def list_by_role(self, role: UserRole | None, skip: int = 0, limit: int = 50) -> tuple[list[User], int]:
        """Return paginated users, optionally filtered by role."""
        query = select(User)
        count_query = select(func.count(User.id))

        if role:
            query = query.where(User.role == role)
            count_query = count_query.where(User.role == role)

        total = (await self._db.execute(count_query)).scalar_one()
        result = await self._db.execute(query.offset(skip).limit(limit))
        return result.scalars().all(), total

    async def create(self, data: UserCreate) -> User:
        """Create a User row and the role-specific profile row atomically."""
        
        # Auto-resolve department string to ID
        if data.department and not data.department_id:
            dept_result = await self._db.execute(select(Department).where(Department.name == data.department))
            dept = dept_result.scalar_one_or_none()
            if not dept:
                dept = Department(name=data.department)
                self._db.add(dept)
                await self._db.flush()
            data.department_id = dept.id

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
        )
        self._db.add(user)
        await self._db.flush()  # Flush to get user.id before creating profile

        if data.role == UserRole.STUDENT:
            student = Student(
                user_id=user.id,
                roll_number=data.roll_number or "",
                course=data.course or "",
                semester=data.semester or "",
                department_id=data.department_id or "",
            )
            self._db.add(student)
        elif data.role in (UserRole.STAFF, UserRole.HOD):
            staff = Staff(
                user_id=user.id,
                department_id=data.department_id or "",
                designation=data.designation or "Lecturer",
            )
            self._db.add(staff)

        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def update_active(self, user: User, is_active: bool) -> User:
        user.is_active = is_active
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self._db.delete(user)
        await self._db.commit()
