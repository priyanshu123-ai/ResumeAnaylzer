"""
auth.py — Authentication Routes
================================
POST /auth/signup     — Register new user
POST /auth/login      — Login and get JWT
GET  /auth/me         — Get current user profile
PUT  /auth/profile    — Update profile
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.database.schemas import (
    UserSignup, UserLogin, TokenResponse,
    UserOut, UserProfileUpdate, MessageResponse
)
from backend.controllers.auth_controller import register_user, login_user, update_profile
from backend.utils.auth_utils import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserOut, status_code=201)
def signup(payload: UserSignup, db: Session = Depends(get_db)):
    """
    Register a new user account.
    Password must be 8+ chars with uppercase and a digit.
    """
    user = register_user(payload, db)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate and receive a JWT access token.
    Include token in future requests: Authorization: Bearer <token>
    """
    return login_user(payload, db)


@router.get("/me", response_model=UserOut)
def get_me(current_user=Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return current_user


@router.put("/profile", response_model=UserOut)
def update_my_profile(
    payload: UserProfileUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the current user's profile (name, phone, location, bio)."""
    return update_profile(current_user, payload, db)
