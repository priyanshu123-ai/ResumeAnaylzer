"""
interview_prep.py — Interview Preparation Page
================================================
AI-generated interview questions, tips, and skill recommendations.
"""

import streamlit as st
from frontend.utils.api_client import (
    list_resumes, generate_interview_tips, predict_skills, APIError
)
from frontend.components.cards import (
    render_hero_banner, render_alert, render_section_heading, render_keyword_tags
)


def show():
    """Render the interview preparation page."""
    render_hero_banner(
        "Interview Preparation",
        "Get personalized interview questions, tips, and skill recommendations powered by Gemini AI.",
        "🎯"
    )

    try:
        resumes = list_resumes()
    except APIError as e:
        render_alert(e.message, "danger")
        return

    if not resumes:
        render_alert("Upload a resume first to get interview tips.", "warning")
        return

    tab_tips, tab_skills = st.tabs(["🎤 Interview Tips", "📚 Skill Recommendations"])

    # ──────────────── INTERVIEW TIPS TAB ──────────────────────
    with tab_tips:
        render_section_heading("Configure Interview Prep", "⚙️")

        resume_map = {r["filename"]: r["id"] for r in resumes}
        selected = st.selectbox("Select Resume", options=list(resume_map.keys()), key="it_resume")
        resume_id = resume_map[selected]

        col1, col2 = st.columns(2)
        with col1:
            job_title = st.text_input("Job Title *", placeholder="e.g. Data Scientist", key="it_title")
        with col2:
            experience = st.selectbox("Experience Level", ["Any", "Junior", "Mid-Level", "Senior"], key="it_exp")

        jd = st.text_area(
            "Job Description (optional but recommended)",
            placeholder="Paste the job description for targeted questions...",
            height=130, key="it_jd"
        )

        if st.button("🎯 Generate Interview Tips", type="primary", use_container_width=True):
            if not job_title:
                render_alert("Please enter the job title.", "warning")
            else:
                jd_text = jd or f"{experience} {job_title} position requiring strong technical skills."
                with st.spinner("🤖 Generating interview preparation guide..."):
                    try:
                        result = generate_interview_tips(resume_id, job_title, jd_text)
                        tips = result.get("interview_tips", "")

                        render_alert("✅ Interview guide ready!", "success")
                        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
                        render_section_heading("Your Interview Preparation Guide", "📋")

                        st.markdown(f"""
                        <div style="background:#1A1A2E; border:1px solid rgba(108,99,255,0.2);
                            border-radius:16px; padding:1.75rem; line-height:1.8;
                            color:#E2E8F0; font-size:0.9rem; white-space:pre-wrap;">
                        {tips}
                        </div>
                        """, unsafe_allow_html=True)

                        st.download_button(
                            "📥 Download Interview Guide",
                            data=tips,
                            file_name=f"interview_prep_{job_title.replace(' ','_')}.txt",
                            mime="text/plain",
                            use_container_width=True,
                        )
                    except APIError as e:
                        render_alert(e.message, "danger")

    # ──────────────── SKILL RECOMMENDATIONS TAB ───────────────
    with tab_skills:
        render_section_heading("Skill Gap Analysis & Recommendations", "📚")

        resume_map2 = {r["filename"]: r["id"] for r in resumes}
        selected2 = st.selectbox("Select Resume", options=list(resume_map2.keys()), key="sk_resume")
        resume_id2 = resume_map2[selected2]
        job_title2 = st.text_input(
            "Target Job Title", placeholder="e.g. DevOps Engineer", key="sk_title"
        )

        if st.button("📊 Analyze Skill Gaps", type="primary", use_container_width=True):
            if not job_title2:
                render_alert("Enter a job title to analyze skill gaps.", "warning")
            else:
                with st.spinner("Analyzing skill gaps..."):
                    try:
                        result = predict_skills(resume_id2, job_title2)

                        render_alert(
                            f"Skill match for {result.get('role','')}: "
                            f"{result.get('match_percentage',0):.0f}%",
                            "info"
                        )

                        col1, col2 = st.columns(2)
                        with col1:
                            render_section_heading("✅ Skills You Have", "")
                            render_keyword_tags(result.get("current_skills") or [], "success")

                            render_section_heading("⚠️ Missing Essential Skills", "")
                            render_keyword_tags(result.get("missing_essential") or [], "danger")

                        with col2:
                            render_section_heading("🚀 Advanced Skills to Learn", "")
                            render_keyword_tags(result.get("missing_advanced") or [], "warning")

                            render_section_heading("🎓 Recommended Certifications", "")
                            certs = result.get("certifications") or []
                            for cert in certs:
                                st.markdown(f"""
                                <div style="padding:0.5rem 0.75rem; background:rgba(108,99,255,0.1);
                                    border-radius:8px; margin-bottom:0.4rem;
                                    color:#A78BFA; font-size:0.85rem;">
                                    🏅 {cert}
                                </div>
                                """, unsafe_allow_html=True)

                    except APIError as e:
                        render_alert(e.message, "danger")

        # ── Learning Resources ─────────────────────────────────
        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
        render_section_heading("Top Learning Resources", "🌐")
        resources = [
            ("Coursera", "courses.coursera.org", "#0056D2", "University-backed courses"),
            ("Udemy", "udemy.com", "#A435F0", "Affordable practical courses"),
            ("LeetCode", "leetcode.com", "#FFA116", "DSA & interview practice"),
            ("HuggingFace", "huggingface.co", "#FF9D00", "ML & NLP learning"),
            ("freeCodeCamp", "freecodecamp.org", "#0A0A23", "Free coding courses"),
        ]
        for name, url, color, desc in resources:
            st.markdown(f"""
            <a href="https://{url}" target="_blank" style="text-decoration:none;">
                <div style="display:flex;align-items:center;gap:1rem;
                    padding:0.75rem 1rem; background:rgba(255,255,255,0.03);
                    border-radius:10px; margin-bottom:0.5rem;
                    border:1px solid rgba(255,255,255,0.06);
                    transition:all 0.2s;" class="glass-card">
                    <div style="width:36px;height:36px;border-radius:8px;
                        background:{color}22;display:flex;align-items:center;
                        justify-content:center;font-weight:700;color:{color};font-size:0.8rem;">
                        {name[0]}
                    </div>
                    <div>
                        <div style="color:#E2E8F0;font-weight:600;font-size:0.9rem;">{name}</div>
                        <div style="color:#64748B;font-size:0.78rem;">{desc}</div>
                    </div>
                </div>
            </a>
            """, unsafe_allow_html=True)
