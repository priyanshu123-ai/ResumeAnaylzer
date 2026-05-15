"""
resume_controller.py — Resume CRUD Business Logic
==================================================
Handles resume upload, listing, deletion, and history.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.database.models import Resume, User
from backend.services.pdf_service import extract_text_from_file, save_uploaded_file, delete_file
from backend.services.nlp_service import full_nlp_analysis, extract_skills
from backend.utils.validators import validate_resume_file
from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def upload_resume(
    upload_file: UploadFile,
    user: User,
    db: Session
) -> Resume:
    """
    Handle resume file upload:
    1. Validate file type and size
    2. Save to disk
    3. Extract text (PDF/DOCX)
    4. Run NLP analysis (entities, skills)
    5. Store everything in DB

    Args:
        upload_file: Incoming file from the API.
        user: Authenticated user.
        db: Database session.

    Returns:
        Created Resume ORM object.
    """
    # Step 1: Validate file
    file_type = validate_resume_file(upload_file, settings.max_file_size_bytes)

    # Step 2: Save to disk
    try:
        stored_path, file_bytes, file_size = await save_uploaded_file(
            upload_file, user.id, file_type
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                           detail=f"Failed to save file: {e}")

    # Step 3: Extract text
    try:
        raw_text = extract_text_from_file(file_bytes, file_type)
    except RuntimeError as e:
        # Clean up saved file if text extraction fails
        delete_file(stored_path)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    if not raw_text or len(raw_text.strip()) < 50:
        delete_file(stored_path)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract meaningful text from the resume. "
                   "Ensure the file is not scanned/image-only."
        )

    # Step 4: NLP analysis
    nlp_result = {}
    try:
        nlp_result = full_nlp_analysis(raw_text)
    except Exception as e:
        logger.warning(f"NLP analysis failed (non-critical): {e}")

    # Step 5: Save to database
    resume = Resume(
        user_id=user.id,
        filename=upload_file.filename,
        stored_path=stored_path,
        file_type=file_type,
        file_size=file_size,
        raw_text=raw_text,
        extracted_skills=nlp_result.get("skills", []),
        extracted_name=nlp_result.get("name"),
        extracted_email=nlp_result.get("email"),
        extracted_phone=nlp_result.get("phone"),
        word_count=nlp_result.get("word_count", len(raw_text.split())),
        uploaded_at=datetime.utcnow(),
        is_active=True,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    logger.info(f"Resume uploaded: id={resume.id}, user={user.email}, file={upload_file.filename}")
    return resume


def get_user_resumes(user: User, db: Session) -> List[Resume]:
    """Return all active resumes for a user (resume history)."""
    return (
        db.query(Resume)
        .filter(Resume.user_id == user.id, Resume.is_active == True)
        .order_by(Resume.uploaded_at.desc())
        .all()
    )


def get_resume_by_id(resume_id: int, user: User, db: Session) -> Resume:
    """
    Fetch a specific resume, ensuring it belongs to the requesting user.

    Raises:
        HTTP 404 if not found.
        HTTP 403 if owned by another user (non-admin).
    """
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    if resume.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")
    return resume


def delete_resume(resume_id: int, user: User, db: Session) -> dict:
    """
    Soft-delete a resume (marks is_active=False) and removes the file.

    Returns:
        Success message dict.
    """
    resume = get_resume_by_id(resume_id, user, db)

    # Delete physical file
    delete_file(resume.stored_path)

    # Soft delete in DB
    resume.is_active = False
    db.commit()

    logger.info(f"Resume deleted: id={resume_id} by user={user.email}")
    return {"message": f"Resume '{resume.filename}' deleted successfully."}


def get_all_resumes_admin(db: Session, skip: int = 0, limit: int = 100) -> List[Resume]:
    """Return all resumes (admin only)."""
    return db.query(Resume).order_by(Resume.uploaded_at.desc()).offset(skip).limit(limit).all()
