"""
dashboard.py — Main Dashboard Page
=====================================
Overview of ATS scores, skills, history charts, and quick stats.
"""

import streamlit as st
from frontend.utils.api_client import list_reports, list_resumes, APIError
from frontend.utils.session import get_user_name, is_admin
from frontend.components.cards import (
    render_hero_banner, render_metric_card, render_alert,
    render_section_heading, render_score_badge
)
from frontend.components.charts import historical_scores_chart, ats_gauge_chart


def show():
    """Render the main user dashboard."""
    name = get_user_name()
    render_hero_banner(
        f"Welcome back, {name.split()[0]}! 👋",
        "Here's an overview of your resume performance and analysis history.",
        "📊"
    )

    # ── Load data ──────────────────────────────────────────────
    try:
        resumes = list_resumes()
        reports = list_reports()
    except APIError as e:
        render_alert(e.message, "danger")
        resumes, reports = [], []

    # ── Top Metric Cards ───────────────────────────────────────
    render_section_heading("Your Stats", "📈")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card(str(len(resumes)), "Resumes Uploaded", "📄", "#6C63FF")
    with col2:
        render_metric_card(str(len(reports)), "Analyses Run", "⚡", "#10B981")
    with col3:
        avg_score = 0.0
        if reports:
            avg_score = sum(r.get("ats_score", 0) or 0 for r in reports) / len(reports)
        render_metric_card(f"{avg_score:.0f}%", "Avg ATS Score", "🎯", "#F59E0B")
    with col4:
        best = max((r.get("ats_score", 0) or 0 for r in reports), default=0)
        render_metric_card(f"{best:.0f}%", "Best Score", "🏆", "#EF4444")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Score History Chart ────────────────────────────────────
    render_section_heading("ATS Score History", "📉")
    report_list = [
        {"created_at": r.get("created_at", ""), "ats_score": r.get("ats_score", 0)}
        for r in reports
    ]
    st.plotly_chart(
        historical_scores_chart(report_list),
        use_container_width=True,
        config={"displayModeBar": False}
    )

    # ── Recent Reports ─────────────────────────────────────────
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    render_section_heading("Recent Analyses", "📋")

    if not reports:
        render_alert("No analyses yet. Upload a resume and run your first analysis!", "info")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📤 Upload Resume", use_container_width=True):
                st.session_state.current_page = "upload"
                st.rerun()
        with col_b:
            if st.button("⚡ Analyze Resume", use_container_width=True):
                st.session_state.current_page = "analyze"
                st.rerun()
        return

    for report in reports[:5]:
        score = report.get("ats_score") or 0
        date = (report.get("created_at") or "")[:10]
        rid = report.get("id")
        matched = len(report.get("matched_keywords") or [])
        missing = len(report.get("missing_keywords") or [])
        domain = report.get("resume_classification") or "Unknown"

        if score >= 70:    score_color, score_label = "#10B981", "Excellent"
        elif score >= 50:  score_color, score_label = "#F59E0B", "Good"
        else:              score_color, score_label = "#EF4444", "Needs Work"

        st.markdown(f"""
        <div class="glass-card" style="display:flex; align-items:center; gap:1.5rem;">
            <div style="text-align:center; min-width:80px;">
                <div style="font-family:'Outfit',sans-serif; font-size:2rem;
                            font-weight:800; color:{score_color}; line-height:1;">{score:.0f}%</div>
                <div style="color:{score_color}; font-size:0.7rem; font-weight:600;">{score_label}</div>
            </div>
            <div style="flex:1; border-left:1px solid #2D2D4E; padding-left:1.25rem;">
                <div style="color:#E2E8F0; font-weight:600; font-size:0.95rem;">
                    Analysis #{rid} &nbsp;·&nbsp; <span style="color:#94A3B8">{date}</span>
                </div>
                <div style="color:#64748B; font-size:0.82rem; margin-top:0.3rem;">
                    🏷️ {domain} &nbsp;|&nbsp;
                    ✅ {matched} matched &nbsp;|&nbsp;
                    ❌ {missing} missing
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if len(reports) > 5:
        if st.button(f"View All {len(reports)} Reports →", use_container_width=True):
            st.session_state.current_page = "history"
            st.rerun()

    # ── Quick Actions ──────────────────────────────────────────
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    render_section_heading("Quick Actions", "⚡")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("📤 Upload Resume", use_container_width=True):
            st.session_state.current_page = "upload"; st.rerun()
    with c2:
        if st.button("⚡ Analyze", use_container_width=True):
            st.session_state.current_page = "analyze"; st.rerun()
    with c3:
        if st.button("📝 Cover Letter", use_container_width=True):
            st.session_state.current_page = "cover_letter"; st.rerun()
    with c4:
        if st.button("🎯 Interview Prep", use_container_width=True):
            st.session_state.current_page = "interview_prep"; st.rerun()
