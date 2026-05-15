"""
models.py — SQLAlchemy ORM Models
===================================
Defines all database tables as Python classes.
Tables: users, resumes, job_descriptions, analysis_reports, ats_scores
"""

import json
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, Enum, ForeignKey, JSON
)
from sqlalchemy.orm import relationship

from backend.database.db import Base


# ═══════════════════════════════════════════════════════════════════════════════
# User Model
# ═══════════════════════════════════════════════════════════════════════════════

class User(Base):
    """
    Represents an application user.
    Roles: 'user' (default) or 'admin' (full access).
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(Text, nullable=False)

    # Role controls access to the admin panel
    role = Column(Enum("user", "admin", name="user_role"), default="user", nullable=False)

    # Profile fields
    phone = Column(String(20), nullable=True)
    location = Column(String(150), nullable=True)
    bio = Column(Text, nullable=True)
    profile_picture = Column(String(255), nullable=True)  # Path/URL to avatar

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships — allow user.resumes, user.job_descriptions etc.
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    job_descriptions = relationship("JobDescription", back_populates="user", cascade="all, delete-orphan")
    analysis_reports = relationship("AnalysisReport", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Resume Model
# ═══════════════════════════════════════════════════════════════════════════════

class Resume(Base):
    """
    Stores uploaded resume files and their extracted text.
    One user can have many resumes (resume history feature).
    """
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    filename = Column(String(255), nullable=False)        # Original filename
    stored_path = Column(String(500), nullable=False)     # Path on disk
    file_type = Column(String(10), nullable=False)        # 'pdf' or 'docx'
    file_size = Column(Integer, nullable=True)            # Size in bytes

    raw_text = Column(Text(length=4294967295), nullable=True)  # Full extracted text (LONGTEXT)
    extracted_skills = Column(JSON, nullable=True)             # List of detected skills
    extracted_name = Column(String(150), nullable=True)        # NER-detected candidate name
    extracted_email = Column(String(120), nullable=True)
    extracted_phone = Column(String(30), nullable=True)
    word_count = Column(Integer, nullable=True)

    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True)  # Soft delete

    # Relationships
    user = relationship("User", back_populates="resumes")
    analysis_reports = relationship("AnalysisReport", back_populates="resume")

    def __repr__(self):
        return f"<Resume id={self.id} filename={self.filename} user_id={self.user_id}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Job Description Model
# ═══════════════════════════════════════════════════════════════════════════════

class JobDescription(Base):
    """
    Stores job descriptions pasted by users for resume matching.
    """
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(200), nullable=False)     # e.g. "Senior Python Developer"
    company = Column(String(150), nullable=True)
    content = Column(Text(length=4294967295), nullable=False)   # Full JD text
    required_skills = Column(JSON, nullable=True)               # Extracted required skills
    experience_level = Column(String(50), nullable=True)        # junior/mid/senior

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="job_descriptions")
    analysis_reports = relationship("AnalysisReport", back_populates="job_description")

    def __repr__(self):
        return f"<JobDescription id={self.id} title={self.title}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Analysis Report Model
# ═══════════════════════════════════════════════════════════════════════════════

class AnalysisReport(Base):
    """
    Stores the full analysis result for a resume vs job description.
    This is the core output of the AI analysis pipeline.
    """
    __tablename__ = "analysis_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    jd_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True)

    # Scores (0.0 to 100.0)
    ats_score = Column(Float, default=0.0)
    skill_match_score = Column(Float, default=0.0)
    keyword_match_score = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)

    # Analysis data stored as JSON
    matched_keywords = Column(JSON, nullable=True)    # Keywords found in both
    missing_keywords = Column(JSON, nullable=True)    # Keywords in JD but not resume
    extra_keywords = Column(JSON, nullable=True)      # Keywords in resume not in JD
    skill_gaps = Column(JSON, nullable=True)          # Skills to learn
    suggestions = Column(JSON, nullable=True)         # Improvement tips list

    # AI-generated text (from Gemini)
    gemini_feedback = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    interview_tips = Column(Text, nullable=True)
    cover_letter = Column(Text, nullable=True)

    # NLP outputs
    resume_classification = Column(String(100), nullable=True)  # e.g. "Data Science"
    candidate_rank = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="analysis_reports")
    resume = relationship("Resume", back_populates="analysis_reports")
    job_description = relationship("JobDescription", back_populates="analysis_reports")
    ats_score_detail = relationship("ATSScore", back_populates="report", uselist=False)

    def __repr__(self):
        return f"<AnalysisReport id={self.id} ats={self.ats_score} user_id={self.user_id}>"


# ═══════════════════════════════════════════════════════════════════════════════
# ATS Score Detail Model
# ═══════════════════════════════════════════════════════════════════════════════

class ATSScore(Base):
    """
    Granular ATS score breakdown for a single analysis report.
    Helps show which specific areas of the resume need improvement.
    """
    __tablename__ = "ats_scores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("analysis_reports.id", ondelete="CASCADE"), nullable=False)

    # Component scores (each out of 100)
    keyword_score = Column(Float, default=0.0)     # How many JD keywords match
    format_score = Column(Float, default=0.0)      # Resume format quality
    section_score = Column(Float, default=0.0)     # Sections present (Summary, Skills, Exp.)
    length_score = Column(Float, default=0.0)      # Resume length appropriateness
    action_verb_score = Column(Float, default=0.0) # Use of strong action verbs

    total_score = Column(Float, default=0.0)       # Weighted average

    # Detailed feedback per component
    keyword_feedback = Column(Text, nullable=True)
    format_feedback = Column(Text, nullable=True)
    section_feedback = Column(Text, nullable=True)

    # Relationship
    report = relationship("AnalysisReport", back_populates="ats_score_detail")

    def __repr__(self):
        return f"<ATSScore id={self.id} total={self.total_score} report_id={self.report_id}>"
