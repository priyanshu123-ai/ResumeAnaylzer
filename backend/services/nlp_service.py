"""
nlp_service.py — Hugging Face NLP Service
==========================================
NLP features powered by spaCy and Hugging Face Transformers:
  - Named Entity Recognition (NER) for contact info
  - Skill extraction from resume text
  - Text summarization
  - Resume classification
"""

import re
from typing import Dict, List, Optional, Any

from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# ── Global NLP model handles (lazy-loaded) ───────────────────────────────────
_spacy_nlp = None
_summarizer = None
_ner_pipeline = None

# ── Comprehensive skill taxonomy ─────────────────────────────────────────────
TECH_SKILLS = {
    # Programming Languages
    "python","java","javascript","typescript","c++","c#","go","rust","kotlin","swift",
    "r","scala","php","ruby","perl","bash","powershell","sql","matlab",
    # Web Technologies
    "html","css","react","angular","vue","next.js","node.js","django","flask","fastapi",
    "spring","express","graphql","rest api","webpack","sass",
    # Data Science / ML
    "machine learning","deep learning","tensorflow","pytorch","keras","scikit-learn",
    "pandas","numpy","matplotlib","seaborn","nlp","computer vision","opencv","hugging face",
    # Cloud / DevOps
    "aws","gcp","azure","docker","kubernetes","terraform","ansible","jenkins","github actions",
    "ci/cd","linux","nginx","apache","redis","rabbitmq","kafka",
    # Databases
    "mysql","postgresql","mongodb","redis","elasticsearch","sqlite","oracle","dynamodb",
    "cassandra","neo4j","bigquery","snowflake",
    # Tools
    "git","github","gitlab","jira","confluence","figma","postman","swagger",
    "jupyter","vscode","intellij","vim",
    # Soft Skills
    "leadership","communication","teamwork","problem solving","agile","scrum",
    "project management","mentoring","critical thinking",
}


def _load_spacy():
    """Lazy-load spaCy NLP model."""
    global _spacy_nlp
    if _spacy_nlp is not None:
        return _spacy_nlp
    if settings.SKIP_HF_MODELS:
        return None
    try:
        import spacy
        _spacy_nlp = spacy.load("en_core_web_sm")
        logger.info("[OK] spaCy model loaded (en_core_web_sm)")
    except OSError:
        logger.warning("spaCy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")
        _spacy_nlp = None
    return _spacy_nlp


def _load_summarizer():
    """Lazy-load HuggingFace summarization pipeline."""
    global _summarizer
    if _summarizer is not None:
        return _summarizer
    if settings.SKIP_HF_MODELS:
        return None
    try:
        from transformers import pipeline
        _summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=-1  # CPU
        )
        logger.info("[OK] HuggingFace summarizer loaded (bart-large-cnn)")
    except Exception as e:
        logger.warning(f"Could not load HF summarizer: {e}")
        _summarizer = None
    return _summarizer


# ═══════════════════════════════════════════════════════════════════════════════
# Named Entity Recognition
# ═══════════════════════════════════════════════════════════════════════════════

def extract_entities(text: str) -> Dict[str, Any]:
    """
    Extract named entities from resume text using spaCy NER.
    Detects: PERSON, ORG, GPE (location), PRODUCT, etc.

    Returns:
        Dict with entity types and extracted values.
    """
    result: Dict[str, Any] = {
        "name": None,
        "organizations": [],
        "locations": [],
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None,
    }

    # Always extract contact info with regex (fast, reliable)
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    phone_match = re.search(r"(\+?[\d\-\.\s\(\)]{10,15})", text)
    linkedin_match = re.search(r"linkedin\.com/in/[\w\-]+", text, re.I)
    github_match = re.search(r"github\.com/[\w\-]+", text, re.I)

    if email_match:
        result["email"] = email_match.group()
    if phone_match:
        result["phone"] = phone_match.group().strip()
    if linkedin_match:
        result["linkedin"] = "https://" + linkedin_match.group()
    if github_match:
        result["github"] = "https://" + github_match.group()

    # Use spaCy for person name and org detection
    nlp = _load_spacy()
    if nlp:
        try:
            doc = nlp(text[:2000])  # Process first 2000 chars for speed
            for ent in doc.ents:
                if ent.label_ == "PERSON" and not result["name"]:
                    result["name"] = ent.text.strip()
                elif ent.label_ == "ORG":
                    if ent.text.strip() not in result["organizations"]:
                        result["organizations"].append(ent.text.strip())
                elif ent.label_ == "GPE":
                    if ent.text.strip() not in result["locations"]:
                        result["locations"].append(ent.text.strip())
        except Exception as e:
            logger.warning(f"spaCy NER failed: {e}")
    else:
        # Fallback: heuristic name extraction (first line with title case)
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for line in lines[:5]:
            words = line.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w.isalpha()):
                result["name"] = line
                break

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Skill Extraction
# ═══════════════════════════════════════════════════════════════════════════════

def extract_skills(text: str) -> List[str]:
    """
    Extract technical and soft skills from resume text.
    Uses a curated skill taxonomy with regex matching.

    Args:
        text: Resume text.

    Returns:
        List of detected skills (deduplicated, sorted).
    """
    text_lower = text.lower()
    found_skills = set()

    for skill in TECH_SKILLS:
        # Word boundary matching to avoid partial matches
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found_skills.add(skill.title())

    # Also try spaCy noun chunks for additional skill detection
    nlp = _load_spacy()
    if nlp:
        try:
            doc = nlp(text[:3000])
            for chunk in doc.noun_chunks:
                chunk_lower = chunk.text.lower().strip()
                if chunk_lower in TECH_SKILLS:
                    found_skills.add(chunk_lower.title())
        except Exception as e:
            logger.warning(f"spaCy skill extraction failed: {e}")

    skills = sorted(list(found_skills))
    logger.debug(f"Extracted {len(skills)} skills")
    return skills


# ═══════════════════════════════════════════════════════════════════════════════
# Text Summarization
# ═══════════════════════════════════════════════════════════════════════════════

def summarize_resume(text: str, max_length: int = 150) -> str:
    """
    Generate a concise summary of the resume using HuggingFace BART.
    Falls back to extractive summarization if model not available.

    Args:
        text: Full resume text.
        max_length: Max summary token length.

    Returns:
        Summary string.
    """
    # Limit input to avoid BART token limits
    input_text = text[:1024] if len(text) > 1024 else text

    summarizer = _load_summarizer()
    if summarizer:
        try:
            result = summarizer(
                input_text,
                max_length=max_length,
                min_length=40,
                do_sample=False
            )
            return result[0]["summary_text"]
        except Exception as e:
            logger.warning(f"HF summarization failed: {e}")

    # Fallback: extractive — return first meaningful sentences
    sentences = re.split(r"[.!?\n]+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
    return " ".join(sentences[:3]) + "..."


# ═══════════════════════════════════════════════════════════════════════════════
# Full NLP Analysis
# ═══════════════════════════════════════════════════════════════════════════════

def full_nlp_analysis(resume_text: str) -> Dict[str, Any]:
    """
    Run the complete NLP pipeline on a resume.

    Returns:
        Dict with entities, skills, summary, and word count.
    """
    logger.info("Running NLP analysis pipeline...")

    entities = extract_entities(resume_text)
    skills = extract_skills(resume_text)
    summary = summarize_resume(resume_text[:1500])

    return {
        "name": entities.get("name"),
        "email": entities.get("email"),
        "phone": entities.get("phone"),
        "linkedin": entities.get("linkedin"),
        "github": entities.get("github"),
        "organizations": entities.get("organizations", [])[:5],
        "locations": entities.get("locations", [])[:3],
        "skills": skills,
        "summary": summary,
        "word_count": len(resume_text.split()),
    }
