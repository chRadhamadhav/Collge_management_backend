"""
Models package — makes all ORM models importable from a single namespace.
Alembic's env.py imports this to ensure all tables are registered with Base.metadata.
"""
from app.models import (  # noqa: F401
    announcement,
    assignment,
    attendance,
    department,
    exam,
    material,
    staff,
    student,
    subject,
    timetable,
    user,
    event,
)
