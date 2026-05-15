"""
upload.py — Resume Upload Page
================================
Drag-and-drop file upload with real-time text preview.
"""

import streamlit as st
from frontend.utils.api_client import upload_resume, list_resumes, delete_resume, APIError
from frontend.utils.session import get_user_name
from frontend.components.cards import (
    render_hero_banner, render_alert, render_resume_card, render_section_heading
)


def show():
    """Render the resume upload and management page."""
    render_hero_banner(
        "Resume Manager",
        "Upload PDF or DOCX resumes. We'll extract and analyze them automatically.",
        "📄"
    )

    # ── Upload Section ─────────────────────────────────────────
    render_section_heading("Upload New Resume", "📤")

    st.markdown("""
    <div style="background:rgba(108,99,255,0.05); border:2px dashed rgba(108,99,255,0.3);
        border-radius:16px; padding:2rem; text-align:center; margin-bottom:1.5rem;">
        <div style="font-size:2.5rem; margin-bottom:0.5rem;">📁</div>
        <p style="color:#94A3B8; margin:0; font-size:0.95rem;">
            Drag & drop or click to browse your resume file
        </p>
        <p style="color:#64748B; margin:0.3rem 0 0; font-size:0.8rem;">
            Supported: PDF, DOCX — Max size: 10MB
        </p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose resume file",
        type=["pdf", "docx"],
        help="Upload your resume in PDF or DOCX format.",
        label_visibility="collapsed"
    )

    if uploaded_file:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"""
            <div style="padding:1rem; background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3);
                border-radius:12px; text-align:center; margin:0.5rem 0;">
                <span style="font-size:1.5rem;">✅</span>
                <div style="color:#10B981; font-weight:600; margin-top:0.3rem;">{uploaded_file.name}</div>
                <div style="color:#64748B; font-size:0.8rem;">{round(uploaded_file.size/1024, 1)} KB</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🚀 Upload & Analyze", use_container_width=True, type="primary"):
                with st.spinner("📤 Uploading and extracting text..."):
                    try:
                        result = upload_resume(uploaded_file.read(), uploaded_file.name)
                        render_alert(
                            f"✅ Resume uploaded! Extracted {result.get('word_count',0)} words "
                            f"and {len(result.get('extracted_skills') or [])} skills.",
                            "success"
                        )
                        if result.get("extracted_skills"):
                            st.markdown("**Detected Skills:**")
                            skills_html = "".join(
                                f'<span class="tag tag-primary">{s}</span>'
                                for s in (result.get("extracted_skills") or [])[:15]
                            )
                            st.markdown(f'<div class="tag-container">{skills_html}</div>',
                                       unsafe_allow_html=True)
                        st.rerun()
                    except APIError as e:
                        render_alert(e.message, "danger")

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    # ── Existing Resumes ───────────────────────────────────────
    render_section_heading("Your Resumes", "📋")

    with st.spinner("Loading resumes..."):
        try:
            resumes = list_resumes()
        except APIError as e:
            render_alert(e.message, "danger")
            return

    if not resumes:
        render_alert("No resumes uploaded yet. Upload your first resume above!", "info")
        return

    st.caption(f"{len(resumes)} resume(s) in your library")

    for resume in resumes:
        col_card, col_actions = st.columns([4, 1])
        with col_card:
            render_resume_card(resume)
        with col_actions:
            st.markdown("<br><br>", unsafe_allow_html=True)
            rid = resume.get("id")

            if st.button("⚡ Analyze", key=f"analyze_{rid}", use_container_width=True):
                st.session_state.selected_resume_id = rid
                st.session_state.current_page = "analyze"
                st.rerun()

            if st.button("🗑️ Delete", key=f"delete_{rid}", use_container_width=True):
                try:
                    delete_resume(rid)
                    st.success("Resume deleted.")
                    st.rerun()
                except APIError as e:
                    render_alert(e.message, "danger")
