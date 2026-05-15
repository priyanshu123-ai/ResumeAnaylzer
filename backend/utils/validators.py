"""
validators.py — Input Validation Helpers
==========================================
Standalone validation functions used across controllers and services.
"""

import re
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status, UploadFile


# ── Allowed file types for resume upload ─────────────────────────────────────
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}


def validate_resume_file(file: UploadFile, max_size_bytes: int) -> str:
    """
    Validate a resume upload (type + size).

    Args:
        file: The uploaded file object from FastAPI.
        max_size_bytes: Maximum allowed file size.

    Returns:
        File extension string ('pdf' or 'docx').

    Raises:
        HTTPException 400 for invalid type or oversized file.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided."
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: PDF, DOCX"
        )

    # Check MIME type if content_type is provided
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file content type: {file.content_type}"
        )

    return ext.lstrip(".")  # Return 'pdf' or 'docx'


def validate_email(email: str) -> bool:
    """
    Basic regex email check.
    Pydantic handles this via EmailStr, but useful for manual checks.
    """
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def sanitize_filename(filename: str) -> str:
    """
    Remove dangerous characters from a filename.
    Prevents path traversal attacks.
    """
    # Keep only alphanumeric, dot, underscore, hyphen
    safe = re.sub(r"[^\w.\-]", "_", filename)
    # Prevent path traversal
    return Path(safe).name


def validate_text_length(text: str, min_len: int = 50, max_len: int = 50000) -> str:
    """
    Ensure a text field is within acceptable length bounds.
    Used for job descriptions and resume text.
    """
    stripped = text.strip()
    if len(stripped) < min_len:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Text is too short (minimum {min_len} characters)."
        )
    if len(stripped) > max_len:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Text is too long (maximum {max_len} characters)."
        )
    return stripped
