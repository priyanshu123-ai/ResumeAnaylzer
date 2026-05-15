"""
auth_utils.py — Authentication Utilities
=========================================
Handles:
  - Password hashing and verification (bcrypt via passlib)
  - JWT token generation and decoding
  - get_current_user dependency for FastAPI route protection
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.database.db import get_db
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# ── Password hashing context using bcrypt ────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── HTTP Bearer scheme for extracting JWT from Authorization header ──────────
bearer_scheme = HTTPBearer()


# ═══════════════════════════════════════════════════════════════════════════════
# Password Utilities
# ═══════════════════════════════════════════════════════════════════════════════

def hash_password(plain_password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    Always store hashed passwords — never plain text!

    Args:
        plain_password: The raw password from the user.

    Returns:
        A bcrypt hash string.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its bcrypt hash.

    Args:
        plain_password: Raw password to check.
        hashed_password: Stored bcrypt hash from the database.

    Returns:
        True if they match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ═══════════════════════════════════════════════════════════════════════════════
# JWT Utilities
# ═══════════════════════════════════════════════════════════════════════════════

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Payload dict — must include at least {"sub": user_email}.
        expires_delta: Custom expiry duration. Defaults to settings value.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})

    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.debug(f"Created JWT token for subject: {data.get('sub')}")
    return token


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT string to decode.

    Returns:
        The decoded payload as a dict.

    Raises:
        HTTPException 401 if token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise credentials_exception


# ═══════════════════════════════════════════════════════════════════════════════
# FastAPI Dependencies
# ═══════════════════════════════════════════════════════════════════════════════

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    """
    FastAPI dependency — extracts and validates the JWT Bearer token.
    Use as a route dependency to protect endpoints.

    Example:
        @router.get("/me")
        def me(current_user = Depends(get_current_user)):
            return current_user

    Returns:
        The User ORM object for the authenticated user.

    Raises:
        HTTP 401 if token is missing, expired, or invalid.
        HTTP 404 if the user no longer exists in the database.
    """
    # Import here to avoid circular imports
    from backend.database.models import User

    token = credentials.credentials
    payload = decode_access_token(token)
    email: str = payload.get("sub")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated."
        )
    return user


def get_current_admin(current_user=Depends(get_current_user)):
    """
    FastAPI dependency — same as get_current_user but requires admin role.

    Raises:
        HTTP 403 if the user is not an admin.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required."
        )
    return current_user
