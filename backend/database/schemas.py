"""
schemas.py — Pydantic Request/Response Schemas
================================================
Defines data validation shapes for all API endpoints.
Schemas separate the API contract from the database model.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, field_validator


# ═══════════════════════════════════════════════════════════════════════════════
# Auth Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class UserSignup(BaseModel):
    """Request body for POST /auth/signup"""
    name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


class UserLogin(BaseModel):
    """Request body for POST /auth/login"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response body for successful login"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    email: str
    role: str


class UserProfileUpdate(BaseModel):
    """Request body for PUT /auth/profile"""
    name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None


class UserOut(BaseModel):
    """Safe user representation — never returns hashed_password"""
    id: int
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# Resume Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class ResumeOut(BaseModel):
    """Resume response — used in lists and detail views"""
    id: int
    filename: str
    file_type: str
    file_size: Optional[int] = None
    extracted_skills: Optional[List[str]] = None
    extracted_name: Optional[str] = None
    word_count: Optional[int] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# Job Description Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class JobDescriptionCreate(BaseModel):
    """Request body for creating a new job description"""
    title: str
    company: Optional[str] = None
    content: str

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if len(v.strip()) < 50:
            raise ValueError("Job description must be at least 50 characters.")
        return v


class JobDescriptionOut(BaseModel):
    id: int
    title: str
    company: Optional[str] = None
    content: str
    required_skills: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# Analysis Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class AnalysisRequest(BaseModel):
    """Request body for POST /analysis/analyze"""
    resume_id: int
    job_description: str
    job_title: str = "Job Position"
    company: Optional[str] = None


class ATSScoreOut(BaseModel):
    """Detailed ATS score breakdown"""
    keyword_score: float
    format_score: float
    section_score: float
    length_score: float
    action_verb_score: float
    total_score: float
    keyword_feedback: Optional[str] = None
    format_feedback: Optional[str] = None
    section_feedback: Optional[str] = None

    class Config:
        from_attributes = True


class AnalysisReportOut(BaseModel):
    """Full analysis report response"""
    id: int
    resume_id: int
    ats_score: float
    skill_match_score: float
    keyword_match_score: float
    overall_score: float
    matched_keywords: Optional[List[str]] = None
    missing_keywords: Optional[List[str]] = None
    skill_gaps: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None
    gemini_feedback: Optional[str] = None
    ai_summary: Optional[str] = None
    interview_tips: Optional[str] = None
    resume_classification: Optional[str] = None
    ats_score_detail: Optional[ATSScoreOut] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CompareRequest(BaseModel):
    """Request body for multi-resume comparison"""
    resume_ids: List[int]
    job_description: str


class CoverLetterRequest(BaseModel):
    """Request body for cover letter generation"""
    resume_id: int
    job_title: str
    company: str
    job_description: str


class InterviewTipsRequest(BaseModel):
    """Request body for interview prep generation"""
    resume_id: int
    job_title: str
    job_description: str


# ═══════════════════════════════════════════════════════════════════════════════
# Admin Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class AdminUserOut(BaseModel):
    """Extended user info for admin panel"""
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    resume_count: int = 0
    report_count: int = 0

    class Config:
        from_attributes = True


class AnalyticsOut(BaseModel):
    """Platform analytics for the admin dashboard"""
    total_users: int
    total_resumes: int
    total_analyses: int
    avg_ats_score: float
    new_users_today: int
    new_resumes_today: int


# ═══════════════════════════════════════════════════════════════════════════════
# Generic Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class MessageResponse(BaseModel):
    """Generic success/info response"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Generic error response"""
    detail: str
    success: bool = False
