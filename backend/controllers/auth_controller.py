"""
auth_controller.py — Authentication Business Logic
====================================================
Handles user registration, login, profile management.
"""

from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.database.models import User
from backend.database.schemas import UserSignup, UserLogin, UserProfileUpdate
from backend.utils.auth_utils import hash_password, verify_password, create_access_token
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def register_user(payload: UserSignup, db: Session) -> User:
    """
    Register a new user account.

    Steps:
    1. Check email is not already registered
    2. Hash the password
    3. Save user to DB

    Args:
        payload: Signup form data (name, email, password).
        db: Active database session.

    Returns:
        Newly created User ORM object.

    Raises:
        HTTP 409 if email already exists.
    """
    # Check for duplicate email
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Please log in."
        )

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        hashed_password=hash_password(payload.password),
        role="user",
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"New user registered: {user.email} (id={user.id})")
    return user


def login_user(payload: UserLogin, db: Session) -> dict:
    """
    Authenticate a user and return a JWT access token.

    Args:
        payload: Login credentials (email, password).
        db: Active database session.

    Returns:
        Dict with token and user info.

    Raises:
        HTTP 401 if credentials are invalid.
        HTTP 403 if account is deactivated.
    """
    user = db.query(User).filter(User.email == payload.email.lower()).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        # Use the same error message to prevent email enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Contact support."
        )

    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.commit()

    # Generate JWT token with user email as subject
    token = create_access_token(data={"sub": user.email, "role": user.role})

    logger.info(f"User logged in: {user.email}")
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }


def update_profile(user: User, payload: UserProfileUpdate, db: Session) -> User:
    """
    Update user profile fields.

    Args:
        user: Current authenticated user.
        payload: Fields to update (all optional).
        db: Active database session.

    Returns:
        Updated User object.
    """
    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    logger.info(f"Profile updated for user: {user.email}")
    return user


def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    """Return all users (admin only)."""
    return db.query(User).offset(skip).limit(limit).all()


def toggle_user_active(user_id: int, db: Session) -> User:
    """Toggle a user's active status (admin action)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    logger.info(f"User {user.email} active status toggled to {user.is_active}")
    return user
