"""
analysis_controller.py — Analysis Orchestration
================================================
Coordinates the full analysis pipeline:
  ML (TF-IDF/cosine) + NLP + Gemini AI + DB persistence
"""

from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.database.models import (
    AnalysisReport, ATSScore, JobDescription, Resume, User
)
from backend.database.schemas import AnalysisRequest, CompareRequest
from backend.services.ml_service import full_ats_analysis
from backend.services.gemini_service import (
    get_resume_feedback, generate_professional_summary,
    classify_resume_domain
)
from backend.models.resume_classifier import classify_resume
from backend.models.skill_predictor import predict_missing_skills
from backend.models.candidate_ranker import rank_candidates
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def run_full_analysis(
    payload: AnalysisRequest,
    user: User,
    db: Session
) -> AnalysisReport:
    """
    Run the complete AI analysis pipeline for a resume + job description.

    Pipeline steps:
    1. Fetch resume from DB
    2. ML analysis (TF-IDF, cosine similarity, ATS scoring)
    3. Resume classification (ML model)
    4. Skill gap prediction
    5. Gemini AI feedback + summary
    6. Persist all results to DB

    Args:
        payload: AnalysisRequest with resume_id and JD text.
        user: Authenticated user.
        db: Database session.

    Returns:
        Saved AnalysisReport ORM object.
    """
    # Step 1: Get resume
    resume = db.query(Resume).filter(
        Resume.id == payload.resume_id,
        Resume.user_id == user.id,
        Resume.is_active == True
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    if not resume.raw_text:
        raise HTTPException(
            status_code=422,
            detail="Resume has no extracted text. Please re-upload."
        )

    # Step 2: Save job description to DB
    jd_record = JobDescription(
        user_id=user.id,
        title=payload.job_title,
        company=payload.company,
        content=payload.job_description,
        created_at=datetime.utcnow(),
    )
    db.add(jd_record)
    db.flush()  # Get jd_record.id without full commit

    # Step 3: ML analysis (TF-IDF cosine similarity + ATS scoring)
    logger.info(f"Running ML analysis for resume_id={resume.id}")
    ml_result = full_ats_analysis(resume.raw_text, payload.job_description)

    ats_data = ml_result["ats_score"]

    # Step 4: Resume classification
    try:
        classification = classify_resume(resume.raw_text)
        resume_domain = classification.get("domain", "Software Engineering")
    except Exception as e:
        logger.warning(f"Classification failed: {e}")
        resume_domain = "Software Engineering"

    # Step 5: Skill gap prediction
    current_skills = resume.extracted_skills or []
    try:
        skill_prediction = predict_missing_skills(current_skills, payload.job_title)
        skill_gaps = skill_prediction.get("missing_essential", [])
    except Exception as e:
        logger.warning(f"Skill prediction failed: {e}")
        skill_gaps = []

    # Step 6: Gemini AI feedback (non-blocking — continues if Gemini fails)
    gemini_feedback = None
    ai_summary = None
    try:
        gemini_feedback = get_resume_feedback(resume.raw_text, payload.job_title)
        ai_summary = generate_professional_summary(resume.raw_text, payload.job_title)
    except Exception as e:
        logger.warning(f"Gemini API call failed (non-critical): {e}")
        gemini_feedback = "Gemini API not configured. Add GEMINI_API_KEY to .env for AI feedback."

    # Step 7: Create AnalysisReport record
    report = AnalysisReport(
        user_id=user.id,
        resume_id=resume.id,
        jd_id=jd_record.id,
        ats_score=ats_data["total_score"],
        skill_match_score=ml_result["skill_match_score"],
        keyword_match_score=ml_result["keyword_match_score"],
        overall_score=ml_result["overall_score"],
        matched_keywords=ml_result["matched_keywords"],
        missing_keywords=ml_result["missing_keywords"],
        skill_gaps=skill_gaps,
        suggestions=ml_result["suggestions"],
        gemini_feedback=gemini_feedback,
        ai_summary=ai_summary,
        resume_classification=resume_domain,
        created_at=datetime.utcnow(),
    )
    db.add(report)
    db.flush()

    # Step 8: Create ATS score breakdown record
    ats_score_record = ATSScore(
        report_id=report.id,
        keyword_score=ats_data["keyword_score"],
        format_score=ats_data["format_score"],
        section_score=ats_data["section_score"],
        length_score=ats_data["length_score"],
        action_verb_score=ats_data["action_verb_score"],
        total_score=ats_data["total_score"],
        keyword_feedback=ats_data.get("keyword_feedback"),
        format_feedback=ats_data.get("format_feedback"),
        section_feedback=ats_data.get("section_feedback"),
    )
    db.add(ats_score_record)

    db.commit()
    db.refresh(report)

    logger.info(
        f"Analysis complete: report_id={report.id}, "
        f"ATS={report.ats_score}, user={user.email}"
    )
    return report


def get_report_by_id(report_id: int, user: User, db: Session) -> AnalysisReport:
    """Fetch a specific analysis report with ownership check."""
    report = db.query(AnalysisReport).filter(AnalysisReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    if report.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")
    return report


def get_user_reports(user: User, db: Session) -> List[AnalysisReport]:
    """Return all analysis reports for a user."""
    return (
        db.query(AnalysisReport)
        .filter(AnalysisReport.user_id == user.id)
        .order_by(AnalysisReport.created_at.desc())
        .all()
    )


def compare_resumes(payload: CompareRequest, user: User, db: Session) -> dict:
    """
    Compare multiple resumes against a job description and rank them.

    Returns:
        Ranking results dict.
    """
    if len(payload.resume_ids) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 resume IDs to compare.")
    if len(payload.resume_ids) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 resumes can be compared at once.")

    resumes = (
        db.query(Resume)
        .filter(
            Resume.id.in_(payload.resume_ids),
            Resume.user_id == user.id,
            Resume.is_active == True,
        )
        .all()
    )

    if not resumes:
        raise HTTPException(status_code=404, detail="No valid resumes found.")

    resume_dicts = [
        {
            "id": r.id,
            "filename": r.filename,
            "raw_text": r.raw_text or "",
            "extracted_skills": r.extracted_skills or [],
        }
        for r in resumes
    ]

    ranked = rank_candidates(resume_dicts, payload.job_description)
    return {"ranked_resumes": ranked, "total": len(ranked)}


def get_platform_analytics(db: Session) -> dict:
    """Return aggregate analytics for the admin dashboard."""
    from sqlalchemy import func
    from backend.database.models import User as UserModel

    today = datetime.utcnow().date()

    total_users = db.query(func.count(UserModel.id)).scalar()
    total_resumes = db.query(func.count(Resume.id)).scalar()
    total_analyses = db.query(func.count(AnalysisReport.id)).scalar()
    avg_ats = db.query(func.avg(AnalysisReport.ats_score)).scalar() or 0.0
    new_users_today = db.query(func.count(UserModel.id)).filter(
        func.date(UserModel.created_at) == today
    ).scalar()
    new_resumes_today = db.query(func.count(Resume.id)).filter(
        func.date(Resume.uploaded_at) == today
    ).scalar()

    return {
        "total_users": total_users or 0,
        "total_resumes": total_resumes or 0,
        "total_analyses": total_analyses or 0,
        "avg_ats_score": round(float(avg_ats), 1),
        "new_users_today": new_users_today or 0,
        "new_resumes_today": new_resumes_today or 0,
    }
