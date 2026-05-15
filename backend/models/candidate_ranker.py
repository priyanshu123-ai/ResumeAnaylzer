"""
candidate_ranker.py — Candidate Ranking System
================================================
Ranks multiple candidates/resumes for a given job description
using a weighted multi-factor scoring algorithm.
"""

from typing import Dict, List, Any
from backend.services.ml_service import compute_cosine_similarity, extract_keywords
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def rank_candidates(
    resumes: List[Dict[str, Any]],
    jd_text: str
) -> List[Dict[str, Any]]:
    """
    Rank a list of resumes against a job description.

    Args:
        resumes: List of dicts, each with:
                   - 'id': Resume ID
                   - 'filename': Resume filename
                   - 'raw_text': Extracted resume text
                   - 'extracted_skills': List of skills (optional)
                   - 'ats_score': Pre-computed ATS score (optional)
        jd_text: Job description text.

    Returns:
        Resumes sorted by rank score (highest first), each with a 'rank_score' key.
    """
    if not resumes:
        return []

    jd_keywords = set(k.lower() for k in extract_keywords(jd_text, 40))
    scored = []

    for resume in resumes:
        raw_text = resume.get("raw_text", "")
        if not raw_text:
            scored.append({**resume, "rank_score": 0.0, "rank_breakdown": {}})
            continue

        # ── Factor 1: Cosine similarity (40%) ─────────────────
        cosine = compute_cosine_similarity(raw_text, jd_text)

        # ── Factor 2: ATS score from DB if available (30%) ────
        ats = float(resume.get("ats_score", 0) or 0)

        # ── Factor 3: Skill match (20%) ───────────────────────
        skills = resume.get("extracted_skills") or []
        skill_lower = {s.lower() for s in skills}
        skill_match = (
            len(skill_lower & jd_keywords) / max(len(jd_keywords), 1) * 100
        )

        # ── Factor 4: Resume completeness (10%) ───────────────
        word_count = len(raw_text.split())
        completeness = min(100.0, word_count / 5)  # 500+ words = 100%

        # ── Weighted rank score ────────────────────────────────
        rank_score = round(
            cosine * 0.40 +
            ats * 0.30 +
            skill_match * 0.20 +
            completeness * 0.10,
            2
        )

        scored.append({
            **resume,
            "rank_score": rank_score,
            "rank_breakdown": {
                "cosine_similarity": round(cosine, 1),
                "ats_score": round(ats, 1),
                "skill_match": round(skill_match, 1),
                "completeness": round(completeness, 1),
            }
        })

    # Sort descending by rank score
    ranked = sorted(scored, key=lambda x: x["rank_score"], reverse=True)

    # Assign rank positions
    for i, candidate in enumerate(ranked, 1):
        candidate["rank"] = i

    logger.info(f"Ranked {len(ranked)} candidates. Top score: {ranked[0]['rank_score'] if ranked else 0}")
    return ranked


def compare_two_resumes(
    resume1: Dict[str, Any],
    resume2: Dict[str, Any],
    jd_text: str
) -> Dict[str, Any]:
    """
    Compare two resumes head-to-head for a given job description.

    Returns:
        Comparison report with scores and recommendation.
    """
    ranked = rank_candidates([resume1, resume2], jd_text)
    winner = ranked[0]
    loser = ranked[1]

    diff = winner["rank_score"] - loser["rank_score"]
    if diff > 20:
        strength = "Significantly better"
    elif diff > 10:
        strength = "Moderately better"
    else:
        strength = "Marginally better"

    return {
        "winner": winner.get("filename", "Resume 1"),
        "winner_score": winner["rank_score"],
        "loser": loser.get("filename", "Resume 2"),
        "loser_score": loser["rank_score"],
        "strength": strength,
        "score_difference": round(diff, 1),
        "details": ranked,
    }
