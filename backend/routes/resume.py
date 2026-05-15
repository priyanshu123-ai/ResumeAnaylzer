"""
resume.py — Resume Management Routes
======================================
POST /resume/upload    — Upload PDF/DOCX resume
GET  /resume/list      — List user's resumes
GET  /resume/{id}      — Get specific resume
DELETE /resume/{id}    — Delete a resume
"""

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List

from backend.database.db import get_db
from backend.database.schemas import ResumeOut, MessageResponse
from backend.controllers.resume_controller import (
    upload_resume, get_user_resumes, get_resume_by_id, delete_resume
)
from backend.utils.auth_utils import get_current_user

router = APIRouter(prefix="/resume", tags=["Resumes"])


@router.post("/upload", response_model=ResumeOut, status_code=201)
async def upload(
    file: UploadFile = File(..., description="Resume file (PDF or DOCX, max 10MB)"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a resume file.
    Supported formats: PDF, DOCX
    Text is automatically extracted and NLP analysis runs in the background.
    """
    return await upload_resume(file, current_user, db)


@router.get("/list", response_model=List[ResumeOut])
def list_resumes(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return all uploaded resumes for the current user (resume history)."""
    return get_user_resumes(current_user, db)


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(
    resume_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific resume by ID."""
    return get_resume_by_id(resume_id, current_user, db)


@router.delete("/{resume_id}", response_model=MessageResponse)
def remove_resume(
    resume_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a resume (soft-delete). Removes the file from disk too."""
    return delete_resume(resume_id, current_user, db)
