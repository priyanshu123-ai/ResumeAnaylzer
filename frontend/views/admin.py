"""
admin.py — Admin Panel Page
=============================
Full admin dashboard: user management, resume oversight, platform analytics.
Requires admin role.
"""

import streamlit as st
from frontend.utils.api_client import (
    admin_list_users, admin_list_resumes, admin_get_analytics, admin_toggle_user, APIError
)
from frontend.utils.session import is_admin
from frontend.components.cards import (
    render_hero_banner, render_alert, render_metric_card, render_section_heading
)
from frontend.components.charts import admin_bar_chart


def show():
    """Render the admin panel."""
    if not is_admin():
        render_alert("Admin access required. You don't have permission to view this page.", "danger")
        return

    render_hero_banner(
        "Admin Panel",
        "Platform management, user control, and analytics dashboard.",
        "⚙️"
    )

    tab_analytics, tab_users, tab_resumes = st.tabs(
        ["📊 Analytics", "👥 Users", "📄 Resumes"]
    )

    # ──────────────── ANALYTICS TAB ───────────────────────────
    with tab_analytics:
        render_section_heading("Platform Overview", "📈")

        try:
            stats = admin_get_analytics()
        except APIError as e:
            render_alert(e.message, "danger"); return

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_metric_card(str(stats.get("total_users", 0)), "Total Users", "👥", "#6C63FF")
        with col2:
            render_metric_card(str(stats.get("total_resumes", 0)), "Total Resumes", "📄", "#10B981")
        with col3:
            render_metric_card(str(stats.get("total_analyses", 0)), "Total Analyses", "⚡", "#F59E0B")
        with col4:
            render_metric_card(
                f"{stats.get('avg_ats_score', 0):.1f}%", "Avg ATS Score", "🎯", "#EF4444"
            )

        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            render_metric_card(str(stats.get("new_users_today", 0)), "New Users Today", "🆕", "#8B85FF")
        with col_b:
            render_metric_card(str(stats.get("new_resumes_today", 0)), "New Resumes Today", "📤", "#34D399")

        # Summary chart
        st.markdown("<br>", unsafe_allow_html=True)
        chart_data = {
            "Total Users": stats.get("total_users", 0),
            "Total Resumes": stats.get("total_resumes", 0),
            "Total Analyses": stats.get("total_analyses", 0),
        }
        st.plotly_chart(
            admin_bar_chart(chart_data, "Platform Statistics"),
            use_container_width=True, config={"displayModeBar": False}
        )

    # ──────────────── USERS TAB ───────────────────────────────
    with tab_users:
        render_section_heading("Registered Users", "👥")

        try:
            users = admin_list_users()
        except APIError as e:
            render_alert(e.message, "danger"); return

        # Search filter
        search = st.text_input("🔍 Search users by name or email...", key="admin_user_search")
        if search:
            users = [u for u in users
                    if search.lower() in u.get("name","").lower()
                    or search.lower() in u.get("email","").lower()]

        st.caption(f"{len(users)} user(s)")

        for user in users:
            uid = user.get("id")
            name = user.get("name", "?")
            email = user.get("email", "?")
            role = user.get("role", "user")
            active = user.get("is_active", True)
            joined = (user.get("created_at") or "")[:10]

            role_color = "#6C63FF" if role == "admin" else "#64748B"
            status_color = "#10B981" if active else "#EF4444"
            status_text = "Active" if active else "Inactive"

            col_info, col_action = st.columns([5, 1])
            with col_info:
                st.markdown(f"""
                <div style="padding:0.9rem 1rem; background:rgba(255,255,255,0.02);
                    border:1px solid rgba(255,255,255,0.05); border-radius:12px;
                    display:flex; align-items:center; gap:1rem; margin-bottom:0.5rem;">
                    <div style="width:42px;height:42px;border-radius:50%;
                        background:rgba(108,99,255,0.2);display:flex;align-items:center;
                        justify-content:center;font-weight:700;color:#A78BFA;font-size:1rem;
                        flex-shrink:0;">{name[0].upper()}</div>
                    <div style="flex:1;min-width:0;">
                        <div style="font-weight:600;color:#E2E8F0;font-size:0.9rem;">{name}</div>
                        <div style="color:#64748B;font-size:0.78rem;">{email} &nbsp;·&nbsp; Joined {joined}</div>
                    </div>
                    <div style="display:flex;gap:0.5rem;align-items:center;flex-shrink:0;">
                        <span style="padding:0.2rem 0.6rem;border-radius:6px;font-size:0.75rem;
                            font-weight:600;background:rgba({_role_rgba(role_color)},0.15);color:{role_color};">
                            {role.upper()}</span>
                        <span style="padding:0.2rem 0.6rem;border-radius:6px;font-size:0.75rem;
                            font-weight:600;background:rgba({_role_rgba(status_color)},0.15);color:{status_color};">
                            {status_text}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_action:
                action_label = "🚫 Deactivate" if active else "✅ Activate"
                if st.button(action_label, key=f"toggle_{uid}", use_container_width=True):
                    try:
                        res = admin_toggle_user(uid)
                        st.success(res.get("message", "Done"))
                        st.rerun()
                    except APIError as e:
                        render_alert(e.message, "danger")

    # ──────────────── RESUMES TAB ─────────────────────────────
    with tab_resumes:
        render_section_heading("All Uploaded Resumes", "📄")

        try:
            all_resumes = admin_list_resumes()
        except APIError as e:
            render_alert(e.message, "danger"); return

        search_r = st.text_input("🔍 Search resumes...", key="admin_resume_search")
        if search_r:
            all_resumes = [r for r in all_resumes
                          if search_r.lower() in r.get("filename","").lower()]

        st.caption(f"{len(all_resumes)} resume(s)")

        for resume in all_resumes:
            fname = resume.get("filename", "?")
            ftype = (resume.get("file_type") or "pdf").upper()
            words = resume.get("word_count") or 0
            date = (resume.get("uploaded_at") or "")[:10]
            skills = resume.get("extracted_skills") or []
            skill_str = ", ".join(skills[:6]) + ("..." if len(skills) > 6 else "")

            st.markdown(f"""
            <div style="padding:0.8rem 1rem; background:rgba(255,255,255,0.02);
                border:1px solid rgba(255,255,255,0.05); border-radius:12px;
                margin-bottom:0.5rem;">
                <div style="display:flex;align-items:center;gap:0.75rem;">
                    <span style="font-size:1.3rem;">{'📄' if ftype == 'PDF' else '📝'}</span>
                    <div style="flex:1;min-width:0;">
                        <div style="font-weight:600;color:#E2E8F0;font-size:0.88rem;
                            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{fname}</div>
                        <div style="color:#64748B;font-size:0.75rem;">
                            {ftype} · {words} words · {date}
                            {f' · <span style="color:#94A3B8">🔧 {skill_str}</span>' if skill_str else ''}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def _role_rgba(hex_color: str) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16)
    return f"{r},{g},{b}"
