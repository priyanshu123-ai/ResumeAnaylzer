"""
admin.py — Admin Panel Routes
===============================
All routes require admin role.
GET  /admin/users              — List all users
GET  /admin/users/{id}         — User detail
PUT  /admin/users/{id}/toggle  — Activate/deactivate user
GET  /admin/resumes            — List all resumes
GET  /admin/analytics          — Platform analytics
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.database.db import get_db
from backend.database.schemas import UserOut, AnalyticsOut, ResumeOut
from backend.controllers.auth_controller import get_all_users, toggle_user_active
from backend.controllers.resume_controller import get_all_resumes_admin
from backend.controllers.analysis_controller import get_platform_analytics
from backend.utils.auth_utils import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=List[UserOut])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Return all registered users. Admin only."""
    return get_all_users(db, skip=skip, limit=limit)


@router.put("/users/{user_id}/toggle")
def toggle_user(
    user_id: int,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Activate or deactivate a user account. Admin only."""
    user = toggle_user_active(user_id, db)
    status_str = "activated" if user.is_active else "deactivated"
    return {"message": f"User {user.email} has been {status_str}.", "is_active": user.is_active}


@router.get("/resumes", response_model=List[ResumeOut])
def list_all_resumes(
    skip: int = 0,
    limit: int = 100,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Return all uploaded resumes across all users. Admin only."""
    return get_all_resumes_admin(db, skip=skip, limit=limit)


@router.get("/analytics", response_model=AnalyticsOut)
def analytics(
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Return platform-wide analytics. Admin only."""
    return get_platform_analytics(db)
