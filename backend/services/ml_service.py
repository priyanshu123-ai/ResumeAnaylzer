"""
ml_service.py — Machine Learning Analysis Service
===================================================
TF-IDF vectorization, cosine similarity, keyword gap analysis, ATS scoring.
"""

import re
from typing import Dict, List, Tuple, Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.utils.logger import get_logger

logger = get_logger(__name__)

ACTION_VERBS = {
    "achieved","built","created","designed","developed","engineered",
    "implemented","improved","increased","launched","led","managed",
    "optimized","reduced","scaled","shipped","solved","automated","deployed"
}

EXPECTED_SECTIONS = ["experience","education","skills","projects","summary",
                     "objective","certifications","achievements"]

STOP_WORDS = {"and","or","the","is","in","at","of","to","a","an","for",
              "with","on","are","be","this","that","have","has","had"}


def preprocess_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\+\#]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_keywords(text: str, top_n: int = 30) -> List[str]:
    """Extract top keywords from text using TF-IDF."""
    if not text or len(text.strip()) < 20:
        return []
    try:
        vectorizer = TfidfVectorizer(
            max_features=200, stop_words="english",
            ngram_range=(1, 2), min_df=1
        )
        tfidf = vectorizer.fit_transform([preprocess_text(text)])
        names = vectorizer.get_feature_names_out()
        scores = tfidf.toarray()[0]
        ranked = sorted(zip(names, scores), key=lambda x: x[1], reverse=True)
        return [w for w, s in ranked if len(w) > 2 and w not in STOP_WORDS and s > 0][:top_n]
    except Exception as e:
        logger.error(f"Keyword extraction failed: {e}")
        words = re.findall(r"\b[a-zA-Z+#][a-zA-Z0-9+#]{2,}\b", text.lower())
        freq: Dict[str, int] = {}
        for w in words:
            if w not in STOP_WORDS:
                freq[w] = freq.get(w, 0) + 1
        return sorted(freq, key=freq.get, reverse=True)[:top_n]  # type: ignore


def compute_cosine_similarity(resume_text: str, jd_text: str) -> float:
    """Compute TF-IDF cosine similarity between resume and JD (0-100)."""
    if not resume_text.strip() or not jd_text.strip():
        return 0.0
    try:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)
        matrix = vectorizer.fit_transform([preprocess_text(resume_text), preprocess_text(jd_text)])
        sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        return round(float(sim) * 100, 2)
    except Exception as e:
        logger.error(f"Cosine similarity failed: {e}")
        return 0.0


def analyze_keyword_gaps(resume_text: str, jd_text: str) -> Dict[str, List[str]]:
    """Find matched, missing, and extra keywords between resume and JD."""
    r_kw = set(k.lower() for k in extract_keywords(resume_text, 50))
    j_kw = set(k.lower() for k in extract_keywords(jd_text, 50))
    return {
        "matched": sorted(r_kw & j_kw)[:20],
        "missing": sorted(j_kw - r_kw)[:15],
        "extra": sorted(r_kw - j_kw)[:10],
    }


def score_keywords(resume_text: str, jd_text: str) -> Tuple[float, str]:
    gaps = analyze_keyword_gaps(resume_text, jd_text)
    total = len(gaps["matched"]) + len(gaps["missing"])
    if total == 0:
        return 50.0, "Could not extract enough keywords."
    score = round(len(gaps["matched"]) / total * 100, 1)
    if score >= 70:
        fb = f"Good keyword match! {len(gaps['matched'])}/{total} JD keywords found."
    elif score >= 40:
        fb = f"Moderate match. Add: {', '.join(gaps['missing'][:5])}"
    else:
        fb = f"Low match. Missing: {', '.join(gaps['missing'][:8])}"
    return score, fb


def score_format(resume_text: str) -> Tuple[float, str]:
    score, issues = 100.0, []
    wc = len(resume_text.split())
    if wc < 200:
        score -= 20; issues.append("Resume too short (< 200 words).")
    elif wc > 1000:
        score -= 10; issues.append("Resume may be too long (> 1000 words).")
    if not re.search(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", resume_text, re.I):
        score -= 15; issues.append("No email detected.")
    if not re.search(r"(\+?\d[\d\-\.\s]{7,}\d)", resume_text):
        score -= 10; issues.append("No phone number detected.")
    if not re.search(r"[•\-\*▪▸◦]", resume_text):
        score -= 10; issues.append("Use bullet points for better readability.")
    return max(0.0, round(score, 1)), " ".join(issues) or "Format looks good!"


def score_sections(resume_text: str) -> Tuple[float, str]:
    text_lower = resume_text.lower()
    found = [s for s in EXPECTED_SECTIONS if s in text_lower]
    missing = [s for s in ["experience", "education", "skills"] if s not in text_lower]
    score = round(len(found) / len(EXPECTED_SECTIONS) * 100, 1)
    fb = (f"Missing sections: {', '.join(s.title() for s in missing)}"
          if missing else f"All key sections found: {', '.join(s.title() for s in found[:4])}")
    return score, fb


def score_action_verbs(resume_text: str) -> float:
    words = set(resume_text.lower().split())
    return min(100.0, round(len(words & ACTION_VERBS) * 8, 1))


def score_length(resume_text: str) -> float:
    wc = len(resume_text.split())
    if 300 <= wc <= 700: return 100.0
    elif 200 <= wc < 300: return 75.0
    elif 700 < wc <= 1000: return 80.0
    elif wc < 200: return 40.0
    return 60.0


def full_ats_analysis(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """Run the complete ATS scoring pipeline and return full analysis dict."""
    logger.info("Starting full ATS analysis...")
    kw_score, kw_fb = score_keywords(resume_text, jd_text)
    fmt_score, fmt_fb = score_format(resume_text)
    sec_score, sec_fb = score_sections(resume_text)
    av_score = score_action_verbs(resume_text)
    ln_score = score_length(resume_text)
    cosine_score = compute_cosine_similarity(resume_text, jd_text)
    gaps = analyze_keyword_gaps(resume_text, jd_text)

    total = round(kw_score*0.40 + fmt_score*0.20 + sec_score*0.20 + av_score*0.10 + ln_score*0.10, 1)

    suggestions = []
    if gaps["missing"]:
        suggestions.append(f"Add missing keywords: {', '.join(gaps['missing'][:6])}")
    if kw_score < 50:
        suggestions.append("Tailor your resume specifically for this role.")
    if "Missing" in sec_fb:
        suggestions.append(sec_fb)
    if fmt_fb != "Format looks good!":
        suggestions.append(fmt_fb)
    if av_score < 40:
        suggestions.append("Use action verbs: Developed, Optimized, Led, Implemented.")
    suggestions.append("Quantify achievements with metrics (e.g., 'Increased sales by 30%').")
    suggestions.append("Ensure ATS-friendly format without tables or graphics.")

    logger.info(f"ATS complete — total: {total}, keyword: {kw_score}, cosine: {cosine_score}")
    return {
        "ats_score": {
            "keyword_score": kw_score, "format_score": fmt_score, "section_score": sec_score,
            "action_verb_score": av_score, "length_score": ln_score, "total_score": total,
            "keyword_feedback": kw_fb, "format_feedback": fmt_fb, "section_feedback": sec_fb,
        },
        "overall_score": total,
        "skill_match_score": cosine_score,
        "keyword_match_score": kw_score,
        "matched_keywords": gaps["matched"],
        "missing_keywords": gaps["missing"],
        "extra_keywords": gaps["extra"],
        "suggestions": suggestions[:8],
    }
