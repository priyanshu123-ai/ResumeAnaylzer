"""
analyze.py — AI Analysis Page
================================
Main analysis workflow: select resume → paste JD → run analysis → view results.
"""

import streamlit as st
from frontend.utils.api_client import (
    list_resumes, analyze_resume, download_report_pdf, APIError
)
from frontend.utils.session import get_page
from frontend.components.cards import (
    render_hero_banner, render_alert, render_section_heading,
    render_keyword_tags, render_suggestion_list, render_score_badge
)
from frontend.components.charts import (
    ats_gauge_chart, score_breakdown_chart, keyword_donut_chart, skill_radar_chart
)


def show():
    """Render the resume analysis page."""
    render_hero_banner(
        "ATS Resume Analyzer",
        "Paste a job description to get your ATS score, keyword analysis, and AI feedback.",
        "⚡"
    )

    # ── Step 1: Select Resume ──────────────────────────────────
    render_section_heading("Step 1: Select Your Resume", "📄")

    try:
        resumes = list_resumes()
    except APIError as e:
        render_alert(e.message, "danger")
        return

    if not resumes:
        render_alert("No resumes found. Please upload a resume first.", "warning")
        if st.button("📤 Go to Upload Page"):
            st.session_state.current_page = "upload"
            st.rerun()
        return

    resume_options = {
        f"{r['filename']} ({(r.get('word_count') or 0)} words)": r['id']
        for r in resumes
    }

    # Pre-select if coming from upload page
    preselected_idx = 0
    if st.session_state.get("selected_resume_id"):
        ids = list(resume_options.values())
        if st.session_state.selected_resume_id in ids:
            preselected_idx = ids.index(st.session_state.selected_resume_id)

    selected_label = st.selectbox(
        "Choose resume",
        options=list(resume_options.keys()),
        index=preselected_idx,
        label_visibility="collapsed"
    )
    selected_resume_id = resume_options[selected_label]

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    # ── Step 2: Job Description ────────────────────────────────
    render_section_heading("Step 2: Paste Job Description", "📋")

    col_title, col_company = st.columns(2)
    with col_title:
        job_title = st.text_input("Job Title", placeholder="e.g. Senior Python Developer",
                                  key="jd_title")
    with col_company:
        company = st.text_input("Company (optional)", placeholder="e.g. Google",
                                key="jd_company")

    jd_text = st.text_area(
        "Job Description",
        placeholder="Paste the full job description here...\n\nTip: Include requirements, responsibilities, and skills listed in the JD for best results.",
        height=220,
        label_visibility="collapsed",
        key="jd_text"
    )

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    # ── Step 3: Run Analysis ───────────────────────────────────
    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        run_btn = st.button("🚀 Analyze Resume", type="primary", use_container_width=True)
    with col_info:
        st.markdown("""
        <div style="color:#64748B; font-size:0.85rem; padding:0.6rem 0;">
            ⏱️ Analysis takes 10-30 seconds &nbsp;|&nbsp;
            🤖 Powered by TF-IDF + Gemini AI
        </div>
        """, unsafe_allow_html=True)

    if run_btn:
        if not job_title:
            render_alert("Please enter the job title.", "warning")
            return
        if not jd_text or len(jd_text.strip()) < 50:
            render_alert("Please paste a job description (at least 50 characters).", "warning")
            return

        with st.spinner("🤖 Running AI analysis... This may take 20-30 seconds."):
            try:
                report = analyze_resume(
                    resume_id=selected_resume_id,
                    job_description=jd_text,
                    job_title=job_title,
                    company=company or ""
                )
                st.session_state.last_report = report
                st.session_state.last_jd_title = job_title
                render_alert("✅ Analysis complete! Scroll down to view results.", "success")
            except APIError as e:
                render_alert(e.message, "danger")
                return

    # ── Results ───────────────────────────────────────────────
    report = st.session_state.get("last_report")
    if not report:
        return

    st.markdown("---")
    render_section_heading("Analysis Results", "📊")

    # ── Top-level score cards ──────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.plotly_chart(
            ats_gauge_chart(report.get("ats_score", 0), "ATS Score"),
            use_container_width=True, config={"displayModeBar": False}
        )
    with col2:
        render_score_badge(report.get("skill_match_score", 0))
        st.caption("Skill Match (Cosine Similarity)")
    with col3:
        render_score_badge(report.get("keyword_match_score", 0))
        st.caption("Keyword Match")
    with col4:
        render_score_badge(report.get("overall_score", 0))
        st.caption("Overall Score")

    # ── Charts Row ─────────────────────────────────────────────
    ats_detail = report.get("ats_score_detail") or {}
    if ats_detail:
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.plotly_chart(
                score_breakdown_chart(ats_detail),
                use_container_width=True, config={"displayModeBar": False}
            )
        with col_chart2:
            matched = report.get("matched_keywords") or []
            missing = report.get("missing_keywords") or []
            st.plotly_chart(
                keyword_donut_chart(matched, missing),
                use_container_width=True, config={"displayModeBar": False}
            )

    # ── Tabs for detailed results ──────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🔑 Keywords", "💡 Suggestions", "🤖 AI Feedback", "📊 Radar"]
    )

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            render_section_heading("✅ Matched Keywords", "")
            render_keyword_tags(report.get("matched_keywords") or [], "success")
        with c2:
            render_section_heading("❌ Missing Keywords", "")
            render_keyword_tags(report.get("missing_keywords") or [], "danger")

        if report.get("skill_gaps"):
            render_section_heading("📚 Skill Gaps to Address", "")
            render_keyword_tags(report.get("skill_gaps") or [], "warning")

    with tab2:
        render_section_heading("Improvement Suggestions", "💡")
        render_suggestion_list(report.get("suggestions") or [])

    with tab3:
        gemini = report.get("gemini_feedback") or ""
        ai_summary = report.get("ai_summary") or ""
        if ai_summary:
            st.markdown("**📝 Suggested Professional Summary:**")
            st.markdown(f"""
            <div style="background:rgba(108,99,255,0.08); border-left:4px solid #6C63FF;
                padding:1rem 1.25rem; border-radius:0 12px 12px 0; margin-bottom:1rem;">
                <p style="color:#C4B5FD; font-style:italic; margin:0; line-height:1.6;">{ai_summary}</p>
            </div>
            """, unsafe_allow_html=True)
        if gemini:
            st.markdown("**🤖 Gemini AI Resume Feedback:**")
            st.markdown(gemini)
        else:
            render_alert("Add your GEMINI_API_KEY in .env for AI-powered feedback.", "info")

        domain = report.get("resume_classification")
        if domain:
            st.markdown(f"**🏷️ Resume Domain Detected:** `{domain}`")

    with tab4:
        if ats_detail:
            st.plotly_chart(
                skill_radar_chart(ats_detail),
                use_container_width=True, config={"displayModeBar": False}
            )

    # ── Download PDF ───────────────────────────────────────────
    st.markdown("---")
    render_section_heading("Download Report", "📥")
    report_id = report.get("id")
    if report_id:
        if st.button("📥 Download PDF Report", type="primary"):
            with st.spinner("Generating PDF..."):
                try:
                    pdf_bytes = download_report_pdf(report_id)
                    st.download_button(
                        label="💾 Save PDF Report",
                        data=pdf_bytes,
                        file_name=f"ats_report_{report_id}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except APIError as e:
                    render_alert(e.message, "danger")
