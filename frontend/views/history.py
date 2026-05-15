"""
history.py — Resume Analysis History & Comparison
===================================================
Shows all past analyses with detailed view and multi-resume comparison.
"""

import streamlit as st
from frontend.utils.api_client import list_reports, list_resumes, compare_resumes, APIError
from frontend.components.cards import (
    render_hero_banner, render_alert, render_section_heading,
    render_keyword_tags, render_suggestion_list
)
from frontend.components.charts import historical_scores_chart, ats_gauge_chart


def show():
    """Render the analysis history and comparison page."""
    render_hero_banner(
        "Analysis History",
        "View all past analyses, track your progress, and compare resumes.",
        "📚"
    )

    tab_history, tab_compare = st.tabs(["📋 My History", "⚖️ Compare Resumes"])

    # ──────────────── HISTORY TAB ─────────────────────────────
    with tab_history:
        try:
            reports = list_reports()
        except APIError as e:
            render_alert(e.message, "danger"); return

        if not reports:
            render_alert("No analysis history yet. Run your first analysis!", "info")
            return

        # Score trend chart
        st.plotly_chart(
            historical_scores_chart([
                {"created_at": r.get("created_at",""), "ats_score": r.get("ats_score",0)}
                for r in reports
            ]),
            use_container_width=True, config={"displayModeBar": False}
        )

        st.caption(f"Total: {len(reports)} analyses")

        # Report list with expandable details
        for report in reports:
            score = report.get("ats_score") or 0
            date = (report.get("created_at") or "")[:10]
            rid = report.get("id")
            domain = report.get("resume_classification") or "Unknown"

            color = "#10B981" if score >= 70 else ("#F59E0B" if score >= 50 else "#EF4444")

            with st.expander(f"Report #{rid} — {score:.0f}% ATS  |  {date}  |  {domain}", expanded=False):
                c1, c2 = st.columns([1, 2])

                with c1:
                    st.plotly_chart(
                        ats_gauge_chart(score, "ATS Score"),
                        use_container_width=True, config={"displayModeBar": False}
                    )

                with c2:
                    # Score breakdown
                    detail = report.get("ats_score_detail") or {}
                    if detail:
                        metrics = [
                            ("Keyword Match", detail.get("keyword_score", 0)),
                            ("Format", detail.get("format_score", 0)),
                            ("Sections", detail.get("section_score", 0)),
                            ("Action Verbs", detail.get("action_verb_score", 0)),
                            ("Length", detail.get("length_score", 0)),
                        ]
                        for label, val in metrics:
                            clr = "#10B981" if val >= 70 else ("#F59E0B" if val >= 40 else "#EF4444")
                            st.markdown(f"""
                            <div style="display:flex;justify-content:space-between;
                                padding:0.4rem 0; border-bottom:1px solid #2D2D4E;">
                                <span style="color:#94A3B8; font-size:0.85rem;">{label}</span>
                                <span style="color:{clr}; font-weight:600; font-size:0.85rem;">{val:.0f}%</span>
                            </div>
                            """, unsafe_allow_html=True)

                # Keywords
                kw_col1, kw_col2 = st.columns(2)
                with kw_col1:
                    st.markdown("**✅ Matched**")
                    render_keyword_tags(report.get("matched_keywords") or [], "success")
                with kw_col2:
                    st.markdown("**❌ Missing**")
                    render_keyword_tags(report.get("missing_keywords") or [], "danger")

                # Suggestions
                if report.get("suggestions"):
                    st.markdown("**💡 Suggestions**")
                    render_suggestion_list((report.get("suggestions") or [])[:4])

                # AI Feedback
                if report.get("gemini_feedback"):
                    st.markdown("**🤖 AI Feedback**")
                    st.markdown(report["gemini_feedback"])

    # ──────────────── COMPARE TAB ─────────────────────────────
    with tab_compare:
        render_section_heading("Compare Multiple Resumes", "⚖️")
        st.caption("Select 2-5 resumes and paste a job description to rank them.")

        try:
            resumes = list_resumes()
        except APIError as e:
            render_alert(e.message, "danger"); return

        if len(resumes) < 2:
            render_alert("Upload at least 2 resumes to use the comparison feature.", "warning")
            return

        resume_map = {r["filename"]: r["id"] for r in resumes}
        selected = st.multiselect(
            "Select resumes to compare",
            options=list(resume_map.keys()),
            max_selections=5,
            help="Select 2 to 5 resumes"
        )
        jd = st.text_area("Job Description", placeholder="Paste the job description...", height=150)

        if st.button("⚖️ Compare Resumes", type="primary", use_container_width=True):
            if len(selected) < 2:
                render_alert("Select at least 2 resumes.", "warning")
            elif not jd.strip():
                render_alert("Paste a job description.", "warning")
            else:
                ids = [resume_map[name] for name in selected]
                with st.spinner("Ranking resumes..."):
                    try:
                        result = compare_resumes(ids, jd)
                        ranked = result.get("ranked_resumes", [])

                        render_section_heading("Ranking Results", "🏆")
                        for r in ranked:
                            rank = r.get("rank", "?")
                            fname = r.get("filename", "Resume")
                            rs = r.get("rank_score", 0)
                            breakdown = r.get("rank_breakdown", {})
                            medal = ["🥇","🥈","🥉","4️⃣","5️⃣"][min(rank-1, 4)]
                            st.markdown(f"""
                            <div class="glass-card">
                                <div style="display:flex;align-items:center;gap:1.25rem;">
                                    <div style="font-size:2.2rem;">{medal}</div>
                                    <div style="flex:1;">
                                        <div style="font-weight:600;color:#E2E8F0;">#{rank} — {fname}</div>
                                        <div style="color:#6C63FF;font-size:0.85rem;font-weight:600;">
                                            Rank Score: {rs:.1f}%
                                        </div>
                                        <div style="color:#64748B;font-size:0.78rem;margin-top:0.2rem;">
                                            Similarity: {breakdown.get('cosine_similarity',0):.0f}% &nbsp;|&nbsp;
                                            ATS: {breakdown.get('ats_score',0):.0f}% &nbsp;|&nbsp;
                                            Skills: {breakdown.get('skill_match',0):.0f}%
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    except APIError as e:
                        render_alert(e.message, "danger")
