"""
test_ml.py — ML Service Tests
"""

import pytest
from backend.services.ml_service import (
    preprocess_text, extract_keywords, compute_cosine_similarity,
    analyze_keyword_gaps, full_ats_analysis
)
from backend.models.resume_classifier import classify_resume
from backend.models.skill_predictor import predict_missing_skills


SAMPLE_RESUME = """
John Doe | john@example.com | +1-555-123-4567

SUMMARY
Senior Python Developer with 5 years of experience building scalable REST APIs
using FastAPI, Django, and Flask. Expert in PostgreSQL, Redis, and Docker.

SKILLS
Python, FastAPI, Django, PostgreSQL, Redis, Docker, Kubernetes, AWS, Git, Linux, SQL

EXPERIENCE
Backend Engineer — TechCorp (2020-Present)
- Developed and deployed microservices handling 1M+ requests/day
- Optimized database queries, reducing response time by 40%
- Led team of 3 engineers on API platform migration

EDUCATION
B.Tech Computer Science — IIT Delhi (2020)
"""

SAMPLE_JD = """
We are looking for a Senior Python Backend Developer.
Required Skills: Python, FastAPI, PostgreSQL, Docker, Redis, AWS, REST API, Git
5+ years experience with microservices architecture.
Knowledge of Kubernetes and CI/CD is a plus.
"""


def test_preprocess_text():
    result = preprocess_text("Hello World! 123 Python+C++")
    assert result == result.lower()
    assert "hello" in result


def test_extract_keywords():
    kw = extract_keywords(SAMPLE_RESUME)
    assert isinstance(kw, list)
    assert len(kw) > 0
    assert len(kw) <= 30


def test_cosine_similarity_same_text():
    score = compute_cosine_similarity(SAMPLE_RESUME, SAMPLE_RESUME)
    assert score > 90.0  # Same text should be near 100%


def test_cosine_similarity_different_text():
    score = compute_cosine_similarity(SAMPLE_RESUME, "Cooking recipes and restaurant management")
    assert score < 50.0  # Very different texts


def test_keyword_gaps():
    gaps = analyze_keyword_gaps(SAMPLE_RESUME, SAMPLE_JD)
    assert "matched" in gaps
    assert "missing" in gaps
    assert "extra" in gaps
    assert isinstance(gaps["matched"], list)
    # Python appears in both
    matched_lower = [k.lower() for k in gaps["matched"]]
    assert any("python" in k for k in matched_lower)


def test_full_ats_analysis():
    result = full_ats_analysis(SAMPLE_RESUME, SAMPLE_JD)
    assert "overall_score" in result
    assert "ats_score" in result
    assert 0 <= result["overall_score"] <= 100
    assert "suggestions" in result
    assert isinstance(result["suggestions"], list)


def test_resume_classifier():
    result = classify_resume(SAMPLE_RESUME)
    assert "domain" in result
    assert "confidence" in result
    assert result["confidence"] > 0


def test_skill_predictor():
    result = predict_missing_skills(
        ["Python", "Django", "PostgreSQL"],
        "Backend Development"
    )
    assert "missing_essential" in result
    assert "missing_advanced" in result
    assert "match_percentage" in result
    assert isinstance(result["match_percentage"], float)
