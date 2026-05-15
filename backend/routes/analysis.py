"""
analysis.py — Analysis Routes
===============================
POST /analysis/analyze          — Full AI analysis
GET  /analysis/reports          — User's analysis history
GET  /analysis/reports/{id}     — Specific report
POST /analysis/compare          — Compare multiple resumes
GET  /analysis/reports/{id}/pdf — Download PDF report
POST /analysis/cover-letter     — Generate cover letter
POST /analysis/interview-tips   — Generate interview tips
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import io

from backend.database.db import get_db
from backend.database.schemas import (
    AnalysisRequest, AnalysisReportOut, CompareRequest,
    CoverLetterRequest, InterviewTipsRequest, MessageResponse
)
from backend.controllers.analysis_controller import (
    run_full_analysis, get_report_by_id, get_user_reports, compare_resumes
)
from backend.controllers.resume_controller import get_resume_by_id
from backend.services.gemini_service import generate_cover_letter, generate_interview_tips
from backend.services.report_service import generate_analysis_report_pdf
from backend.models.skill_predictor import predict_missing_skills
from backend.utils.auth_utils import get_current_user

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("/analyze", response_model=AnalysisReportOut, status_code=201)
def analyze(
    payload: AnalysisRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run full AI analysis pipeline:
    - TF-IDF cosine similarity
    - ATS scoring (5 components)
    - Keyword gap analysis
    - Gemini AI feedback
    - Resume classification
    - Skill gap prediction
    """
    report = run_full_analysis(payload, current_user, db)
    return report


@router.get("/reports", response_model=List[AnalysisReportOut])
def list_reports(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return all analysis reports for the authenticated user."""
    return get_user_reports(current_user, db)


@router.get("/reports/{report_id}", response_model=AnalysisReportOut)
def get_report(
    report_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific analysis report by ID."""
    return get_report_by_id(report_id, current_user, db)


@router.get("/reports/{report_id}/pdf")
def download_report_pdf(
    report_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download an analysis report as a PDF file."""
    report = get_report_by_id(report_id, current_user, db)

    report_dict = {
        "overall_score": report.overall_score,
        "skill_match_score": report.skill_match_score,
        "keyword_match_score": report.keyword_match_score,
        "ats_score": {
            "keyword_score": report.ats_score_detail.keyword_score if report.ats_score_detail else report.ats_score,
            "format_score": report.ats_score_detail.format_score if report.ats_score_detail else 0,
            "section_score": report.ats_score_detail.section_score if report.ats_score_detail else 0,
            "action_verb_score": report.ats_score_detail.action_verb_score if report.ats_score_detail else 0,
            "length_score": report.ats_score_detail.length_score if report.ats_score_detail else 0,
            "keyword_feedback": report.ats_score_detail.keyword_feedback if report.ats_score_detail else "",
            "format_feedback": report.ats_score_detail.format_feedback if report.ats_score_detail else "",
            "section_feedback": report.ats_score_detail.section_feedback if report.ats_score_detail else "",
        },
        "matched_keywords": report.matched_keywords or [],
        "missing_keywords": report.missing_keywords or [],
        "suggestions": report.suggestions or [],
        "gemini_feedback": report.gemini_feedback or "",
    }

    try:
        pdf_bytes = generate_analysis_report_pdf(
            report_dict,
            user_name=current_user.name,
            job_title=report.job_description.title if report.job_description else "Job Position"
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=resume_analysis_report_{report_id}.pdf"
        }
    )


@router.post("/compare")
def compare(
    payload: CompareRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare multiple resumes against a job description and rank them."""
    return compare_resumes(payload, current_user, db)


@router.post("/cover-letter")
def cover_letter(
    payload: CoverLetterRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a personalized cover letter using Gemini AI."""
    resume = get_resume_by_id(payload.resume_id, current_user, db)
    letter = generate_cover_letter(
        resume.raw_text or "",
        payload.job_title,
        payload.company,
        payload.job_description
    )
    return {"cover_letter": letter}


@router.post("/interview-tips")
def interview_tips(
    payload: InterviewTipsRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate personalized interview preparation tips using Gemini AI."""
    resume = get_resume_by_id(payload.resume_id, current_user, db)
    tips = generate_interview_tips(
        resume.raw_text or "",
        payload.job_title,
        payload.job_description
    )
    return {"interview_tips": tips}


@router.get("/skills/predict")
def predict_skills(
    job_title: str,
    resume_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Predict missing skills for a given job role based on the resume."""
    resume = get_resume_by_id(resume_id, current_user, db)
    current_skills = resume.extracted_skills or []
    return predict_missing_skills(current_skills, job_title)
