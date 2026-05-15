"""
cards.py — Reusable HTML Card Components for Streamlit
"""

import streamlit as st
from typing import List


def _hex_to_rgba(hex_color: str) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"{r},{g},{b}"


def render_hero_banner(title: str, subtitle: str, emoji: str = "🤖") -> None:
    st.markdown(f"""
    <div class="hero-banner fade-in">
        <div style="display:flex; align-items:center; gap:1rem; margin-bottom:0.75rem;">
            <span style="font-size:2.5rem">{emoji}</span>
            <h1 style="margin:0; color:white; font-family:'Outfit',sans-serif;">{title}</h1>
        </div>
        <p style="color:rgba(255,255,255,0.8); margin:0; font-size:1rem;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(value: str, label: str, icon: str = "📊", color: str = "#6C63FF"):
    st.markdown(f"""
    <div class="metric-card fade-in">
        <div style="width:44px;height:44px;border-radius:12px;background:rgba({_hex_to_rgba(color)},0.15);
            display:flex;align-items:center;justify-content:center;font-size:1.4rem;margin:0 auto 0.75rem;">
            {icon}
        </div>
        <span class="metric-value">{value}</span>
        <div class="metric-label">{label}</div>
    </div>""", unsafe_allow_html=True)


def render_score_badge(score: float, size: str = "large") -> None:
    if score >= 70:   color, label = "#10B981", "Excellent"
    elif score >= 50: color, label = "#F59E0B", "Good"
    else:             color, label = "#EF4444", "Needs Work"
    font_size = "3.5rem" if size == "large" else "2rem"
    st.markdown(f"""
    <div style="background:rgba({_hex_to_rgba(color)},0.12);border:1px solid {color}40;
        border-radius:16px;padding:1.5rem;text-align:center;">
        <div style="font-family:'Outfit',sans-serif;font-size:{font_size};font-weight:800;color:{color};line-height:1;">
            {score:.0f}%</div>
        <div style="color:{color};font-size:0.9rem;font-weight:600;margin-top:0.4rem;">{label}</div>
    </div>""", unsafe_allow_html=True)


def render_keyword_tags(keywords: List[str], tag_type: str = "success") -> None:
    if not keywords: st.caption("None found."); return
    tags_html = "".join(f'<span class="tag tag-{tag_type}">{kw}</span>' for kw in keywords)
    st.markdown(f'<div class="tag-container">{tags_html}</div>', unsafe_allow_html=True)


def render_skill_bar(skill: str, percentage: float) -> None:
    color = "#10B981" if percentage >= 70 else ("#F59E0B" if percentage >= 40 else "#EF4444")
    st.markdown(f"""
    <div class="skill-bar-wrap">
        <div class="skill-bar-label">
            <span>{skill}</span>
            <span style="color:{color};font-weight:600">{percentage:.0f}%</span>
        </div>
        <div class="skill-bar-bg">
            <div class="skill-bar-fill" style="width:{percentage}%;background:{color};"></div>
        </div>
    </div>""", unsafe_allow_html=True)


def render_alert(message: str, alert_type: str = "info", icon: str = "") -> None:
    icons = {"success": "✅", "warning": "⚠️", "info": "ℹ️", "danger": "❌"}
    icon = icon or icons.get(alert_type, "ℹ️")
    st.markdown(f"""
    <div class="alert alert-{alert_type}">
        <span style="font-size:1.2rem">{icon}</span>
        <span>{message}</span>
    </div>""", unsafe_allow_html=True)


def render_section_heading(text: str, icon: str = "") -> None:
    st.markdown(f'<div class="section-heading">{icon} {text}</div>', unsafe_allow_html=True)


def render_suggestion_list(suggestions: List[str]) -> None:
    if not suggestions: render_alert("No suggestions at this time.", "info"); return
    for i, s in enumerate(suggestions, 1):
        st.markdown(f"""
        <div style="display:flex;gap:1rem;padding:0.9rem 1rem;background:rgba(108,99,255,0.06);
            border-left:3px solid #6C63FF;border-radius:0 10px 10px 0;margin-bottom:0.6rem;">
            <div style="width:26px;height:26px;border-radius:50%;background:rgba(108,99,255,0.2);
                color:#A78BFA;display:flex;align-items:center;justify-content:center;
                font-size:0.75rem;font-weight:700;flex-shrink:0;">{i}</div>
            <span style="color:#CBD5E1;font-size:0.9rem;line-height:1.5;">{s}</span>
        </div>""", unsafe_allow_html=True)


def render_resume_card(resume: dict) -> None:
    fname = resume.get("filename", "resume.pdf")
    ftype = (resume.get("file_type", "pdf") or "pdf").upper()
    size_kb = round((resume.get("file_size", 0) or 0) / 1024, 1)
    words = resume.get("word_count", 0) or 0
    skills = resume.get("extracted_skills") or []
    date = (resume.get("uploaded_at") or "")[:10]
    icon = "📄" if ftype == "PDF" else "📝"
    skill_preview = ", ".join(skills[:5]) + ("..." if len(skills) > 5 else "")
    st.markdown(f"""
    <div class="glass-card">
        <div style="display:flex;align-items:flex-start;gap:1rem;">
            <div style="font-size:2rem;width:50px;height:50px;display:flex;align-items:center;
                justify-content:center;background:rgba(108,99,255,0.12);border-radius:12px;">
                {icon}</div>
            <div style="flex:1;min-width:0;">
                <div style="font-weight:600;color:#E2E8F0;font-size:1rem;
                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{fname}</div>
                <div style="color:#64748B;font-size:0.8rem;margin-top:0.2rem;">
                    {ftype} • {size_kb} KB • {words} words • Uploaded {date}</div>
                {f'<div style="color:#94A3B8;font-size:0.8rem;margin-top:0.4rem;">🔧 {skill_preview}</div>' if skill_preview else ''}
            </div>
        </div>
    </div>""", unsafe_allow_html=True)
