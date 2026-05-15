"""
gemini_service.py — Google Gemini API Integration
===================================================
All AI-powered features via Google Gemini:
  - Resume feedback and improvement suggestions
  - Professional summary generation
  - Interview preparation tips
  - Cover letter generation
  - Skill recommendations
  - Resume classification
"""

import re
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# ── Initialize Gemini client ──────────────────────────────────────────────────
_gemini_model = None

def _get_model():
    """Lazy-initialize the Gemini model to avoid startup failures."""
    global _gemini_model
    if _gemini_model is None:
        if not settings.gemini_enabled:
            return None
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
            logger.info("[OK] Gemini model initialized (gemini-1.5-flash)")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            return None
    return _gemini_model


def _call_gemini(prompt: str, max_tokens: int = 1024) -> Optional[str]:
    """
    Send a prompt to the Gemini API and return the response text.

    Args:
        prompt: The instruction prompt.
        max_tokens: Approximate response length limit.

    Returns:
        Response text, or None if Gemini is unavailable.
    """
    model = _get_model()
    if not model:
        return None
    try:
        response = model.generate_content(
            prompt,
            generation_config={"max_output_tokens": max_tokens, "temperature": 0.7}
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Resume Feedback
# ═══════════════════════════════════════════════════════════════════════════════

def get_resume_feedback(resume_text: str, job_title: str) -> str:
    """
    Get comprehensive AI feedback on the resume for a given role.

    Returns:
        AI feedback string, or a helpful fallback message.
    """
    prompt = f"""You are an expert resume coach and ATS specialist.

Analyze this resume for a **{job_title}** position and provide:
1. Overall assessment (2-3 sentences)
2. Top 3 strengths of this resume
3. Top 3 areas for improvement
4. Specific action items to make it more ATS-friendly
5. Professional tone and impact score (1-10)

Resume Text:
\"\"\"
{resume_text[:3000]}
\"\"\"

Be specific, actionable, and encouraging. Format with clear sections."""

    result = _call_gemini(prompt, max_tokens=800)
    if result:
        return result
    return _fallback_resume_feedback(job_title)


def _fallback_resume_feedback(job_title: str) -> str:
    return f"""## Resume Feedback for {job_title}

**Overall Assessment:** Your resume has been analyzed using our AI engine.

**Key Recommendations:**
1. Tailor your resume keywords to match the specific job description
2. Quantify achievements with measurable metrics where possible
3. Ensure all relevant skills for {job_title} are prominently listed
4. Use strong action verbs (Developed, Led, Implemented, Optimized)
5. Keep formatting clean and ATS-friendly

*Note: Connect your Gemini API key for personalized AI feedback.*"""


# ═══════════════════════════════════════════════════════════════════════════════
# Professional Summary Generation
# ═══════════════════════════════════════════════════════════════════════════════

def generate_professional_summary(resume_text: str, job_title: str) -> str:
    """Generate a tailored professional summary for the resume."""
    prompt = f"""You are a professional resume writer.

Based on the resume below, write a compelling 3-4 sentence professional summary 
for a **{job_title}** position. The summary should:
- Start with the candidate's experience level and key expertise
- Highlight 2-3 most relevant achievements or skills
- End with what value they bring to the role
- Be written in first person without using "I"
- Be ATS-optimized with relevant keywords

Resume Text:
\"\"\"
{resume_text[:2000]}
\"\"\"

Output ONLY the professional summary paragraph, nothing else."""

    result = _call_gemini(prompt, max_tokens=300)
    return result or f"Results-driven professional with expertise relevant to {job_title}. Proven track record of delivering impactful solutions with strong technical and analytical skills. Committed to driving innovation and excellence in every role."


# ═══════════════════════════════════════════════════════════════════════════════
# Interview Preparation
# ═══════════════════════════════════════════════════════════════════════════════

def generate_interview_tips(resume_text: str, job_title: str, jd_text: str) -> str:
    """Generate personalized interview preparation tips."""
    prompt = f"""You are an expert interview coach.

Based on this candidate's resume and the job description below, generate:
1. **Top 5 likely interview questions** for this {job_title} role
2. **Brief answer tips** for each question based on their resume
3. **3 STAR method example responses** (Situation, Task, Action, Result)
4. **Technical topics** they should prepare for
5. **Questions to ask the interviewer**

Resume Summary:
\"\"\"
{resume_text[:1500]}
\"\"\"

Job Description:
\"\"\"
{jd_text[:1000]}
\"\"\"

Be specific and actionable. Format clearly with numbered sections."""

    result = _call_gemini(prompt, max_tokens=900)
    return result or _fallback_interview_tips(job_title)


def _fallback_interview_tips(job_title: str) -> str:
    return f"""## Interview Preparation for {job_title}

**Likely Questions:**
1. Tell me about yourself and your relevant experience
2. What are your greatest technical strengths for this role?
3. Describe a challenging project and how you overcame it
4. How do you stay updated with industry trends?
5. Where do you see yourself in 5 years?

**STAR Method Tip:** Structure answers as: Situation → Task → Action → Result

**Preparation Checklist:**
- Research the company thoroughly
- Review your resume stories with specific metrics
- Prepare 3-5 questions for the interviewer

*Connect Gemini API for personalized, role-specific interview tips.*"""


# ═══════════════════════════════════════════════════════════════════════════════
# Cover Letter Generation
# ═══════════════════════════════════════════════════════════════════════════════

def generate_cover_letter(
    resume_text: str,
    job_title: str,
    company: str,
    jd_text: str
) -> str:
    """Generate a personalized cover letter."""
    prompt = f"""You are a professional cover letter writer.

Write a compelling, personalized cover letter for:
- Position: **{job_title}**
- Company: **{company}**

Use information from the resume to make it specific and authentic.
The letter should be:
- 3-4 paragraphs, professional tone
- Opening: express enthusiasm for the role and company
- Body: highlight 2-3 most relevant experiences/achievements from resume
- Closing: call to action and professional sign-off
- DO NOT use placeholder text like [Your Name]

Resume:
\"\"\"
{resume_text[:1800]}
\"\"\"

Job Description Summary:
\"\"\"
{jd_text[:800]}
\"\"\"

Write the complete cover letter starting with "Dear Hiring Manager,\""""

    result = _call_gemini(prompt, max_tokens=700)
    return result or f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company}. With my background and experience, I am confident in my ability to make a meaningful contribution to your team.

My experience has equipped me with the technical skills and problem-solving abilities directly relevant to this role. I am particularly drawn to {company}'s reputation for innovation and excellence.

I would welcome the opportunity to discuss how my skills align with your needs. Thank you for your consideration.

Sincerely,
[Your Name]

*Connect Gemini API for a fully personalized cover letter.*"""


# ═══════════════════════════════════════════════════════════════════════════════
# Skill Recommendations
# ═══════════════════════════════════════════════════════════════════════════════

def recommend_skills(job_title: str, current_skills: list) -> str:
    """Recommend skills to learn for a given job role."""
    skills_str = ", ".join(current_skills[:15]) if current_skills else "Not specified"

    prompt = f"""You are a career development expert.

For someone pursuing a **{job_title}** role with these current skills: {skills_str}

Provide:
1. **5 Essential skills** they must learn immediately
2. **5 Advanced skills** for career growth
3. **Recommended certifications** (with providers)
4. **Learning resources** (free and paid) for the top 3 missing skills
5. **Estimated learning timeline** to be job-ready

Be specific with technology names, versions, and platforms. Format clearly."""

    result = _call_gemini(prompt, max_tokens=600)
    return result or f"For a {job_title} role, focus on developing core technical skills in the domain, supplemented by relevant certifications. *Connect Gemini API for personalized skill recommendations.*"


# ═══════════════════════════════════════════════════════════════════════════════
# Resume Classification
# ═══════════════════════════════════════════════════════════════════════════════

def classify_resume_domain(resume_text: str) -> str:
    """Classify the resume into a professional domain/category."""
    prompt = f"""Classify this resume into ONE of these categories:
Software Engineering, Data Science, Machine Learning, DevOps/Cloud,
Cybersecurity, Frontend Development, Backend Development, Full Stack,
Data Engineering, Product Management, Business Analysis, Design/UX,
Marketing, Finance, Healthcare, Other

Resume (first 1000 chars):
\"\"\"
{resume_text[:1000]}
\"\"\"

Respond with ONLY the category name, nothing else."""

    result = _call_gemini(prompt, max_tokens=20)
    if result:
        clean = result.strip().replace("**", "").split("\n")[0]
        return clean[:100]
    return _classify_by_keywords(resume_text)


def _classify_by_keywords(resume_text: str) -> str:
    """Simple keyword-based fallback classification."""
    text = resume_text.lower()
    mapping = {
        "Data Science": ["data science", "machine learning", "tensorflow", "pytorch", "pandas"],
        "Software Engineering": ["software engineer", "java", "c++", "python", "algorithms"],
        "Frontend Development": ["react", "vue", "angular", "html", "css", "javascript", "frontend"],
        "Backend Development": ["django", "fastapi", "flask", "node.js", "backend", "api"],
        "DevOps/Cloud": ["docker", "kubernetes", "aws", "gcp", "azure", "terraform", "devops"],
        "Data Engineering": ["spark", "hadoop", "airflow", "etl", "data pipeline", "kafka"],
        "Cybersecurity": ["security", "penetration", "vulnerability", "siem", "firewall"],
    }
    for domain, keywords in mapping.items():
        if any(kw in text for kw in keywords):
            return domain
    return "Software Engineering"
