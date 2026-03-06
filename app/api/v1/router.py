"""
Main API v1 router — aggregates all feature routers under /api/v1.
"""
from fastapi import APIRouter

from app.api.v1 import admin, auth, hod, staff, student

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(admin.router)
router.include_router(hod.router)
router.include_router(staff.router)
router.include_router(student.router)
