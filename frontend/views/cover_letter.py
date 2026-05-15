"""
cover_letter.py — AI Cover Letter Generator
=============================================
Generates personalized cover letters using Gemini API.
"""

import streamlit as st
from frontend.utils.api_client import list_resumes, generate_cover_letter, APIError
from frontend.components.cards import render_hero_banner, render_alert, render_section_heading


def show():
    """Render the cover letter generator page."""
    render_hero_banner(
        "Cover Letter Generator",
        "Generate a personalized, ATS-optimized cover letter in seconds using Gemini AI.",
        "📝"
    )

    try:
        resumes = list_resumes()
    except APIError as e:
        render_alert(e.message, "danger")
        return

    if not resumes:
        render_alert("Upload a resume first to generate a cover letter.", "warning")
        return

    render_section_heading("Configure Your Cover Letter", "⚙️")

    resume_map = {r["filename"]: r["id"] for r in resumes}
    selected_resume = st.selectbox(
        "Select Resume", options=list(resume_map.keys()), label_visibility="visible"
    )
    resume_id = resume_map[selected_resume]

    col1, col2 = st.columns(2)
    with col1:
        job_title = st.text_input("Job Title *", placeholder="e.g. Senior Data Scientist")
    with col2:
        company = st.text_input("Company Name *", placeholder="e.g. Google")

    jd = st.text_area(
        "Job Description",
        placeholder="Paste the job description for a more tailored cover letter...",
        height=160
    )

    st.markdown("<br>", unsafe_allow_html=True)
    generate_btn = st.button("✨ Generate Cover Letter", type="primary", use_container_width=True)

    if generate_btn:
        if not job_title or not company:
            render_alert("Please fill in the job title and company name.", "warning")
            return

        with st.spinner("🤖 Generating your personalized cover letter..."):
            try:
                result = generate_cover_letter(
                    resume_id=resume_id,
                    job_title=job_title,
                    company=company,
                    jd=jd or f"Position: {job_title} at {company}"
                )
                letter = result.get("cover_letter", "")

                render_alert("✅ Cover letter generated successfully!", "success")

                st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
                render_section_heading("Your Cover Letter", "📄")

                st.markdown(f"""
                <div style="background:#1A1A2E; border:1px solid rgba(108,99,255,0.25);
                    border-radius:16px; padding:2rem; line-height:1.8;
                    color:#E2E8F0; font-size:0.95rem; white-space:pre-wrap;
                    font-family:'Inter',sans-serif;">
                {letter}
                </div>
                """, unsafe_allow_html=True)

                # Copy / Download
                col_copy, col_dl = st.columns(2)
                with col_copy:
                    st.text_area("Copy from here:", value=letter, height=200, label_visibility="collapsed")
                with col_dl:
                    st.download_button(
                        "📥 Download as .txt",
                        data=letter,
                        file_name=f"cover_letter_{company.replace(' ','_')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )

            except APIError as e:
                render_alert(e.message, "danger")

    # ── Tips ──────────────────────────────────────────────────
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    render_section_heading("Cover Letter Tips", "💡")
    tips = [
        "Always customize the letter for each company — avoid generic templates.",
        "Keep it to one page (3-4 paragraphs maximum).",
        "Open with a strong hook — mention a specific achievement.",
        "Mirror keywords from the job description for ATS compatibility.",
        "End with a clear call-to-action requesting an interview.",
    ]
    for tip in tips:
        st.markdown(f"""
        <div style="display:flex;gap:0.75rem;padding:0.6rem 0;
            border-bottom:1px solid rgba(45,45,78,0.5);">
            <span style="color:#6C63FF;">•</span>
            <span style="color:#94A3B8;font-size:0.88rem;">{tip}</span>
        </div>
        """, unsafe_allow_html=True)
