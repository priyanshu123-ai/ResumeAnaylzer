"""
app.py — Streamlit Frontend Entry Point
=========================================
Main application router. Handles:
  - CSS theme injection
  - Session state initialization
  - Sidebar navigation
  - Page routing based on session state
  - Login/logout flow

Run with:
    streamlit run frontend/app.py
"""

import streamlit as st
import sys
import os

# ── Ensure project root is on the Python path ─────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.utils.session import init_session, is_logged_in, is_admin, get_user_name, clear_session

# ── Page config must be the very first Streamlit call ─────────────────────────
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://github.com/your-repo/resume-analyzer",
        "About": "AI Resume Analyzer — Production-grade SaaS resume analysis tool",
    }
)


def load_css():
    """Inject the custom CSS theme from the styles file."""
    css_path = os.path.join(os.path.dirname(__file__), "styles", "theme.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_sidebar():
    """
    Render the sidebar navigation.
    Returns the selected page name.
    """
    with st.sidebar:
        # ── Logo ──────────────────────────────────────────────
        st.markdown("""
        <div style="padding:1rem 0 1.5rem; text-align:center;">
            <div style="font-size:2.2rem; margin-bottom:0.4rem;">🤖</div>
            <div style="font-family:'Outfit',sans-serif; font-size:1.2rem;
                        font-weight:700; color:#E2E8F0;">AI Resume</div>
            <div style="font-family:'Outfit',sans-serif; font-size:1.2rem;
                        font-weight:700; background:linear-gradient(135deg,#6C63FF,#A78BFA);
                        -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                        Analyzer</div>
        </div>
        <hr style="border:none; border-top:1px solid #2D2D4E; margin:0 0 1rem;">
        """, unsafe_allow_html=True)

        # ── User Info ─────────────────────────────────────────
        name = get_user_name()
        role = st.session_state.get("user_role", "user")
        email = st.session_state.get("user_email", "")

        st.markdown(f"""
        <div style="background:rgba(108,99,255,0.1); border:1px solid rgba(108,99,255,0.2);
            border-radius:12px; padding:0.9rem 1rem; margin-bottom:1.25rem;">
            <div style="display:flex; align-items:center; gap:0.75rem;">
                <div style="width:36px; height:36px; border-radius:50%;
                    background:linear-gradient(135deg,#6C63FF,#A78BFA);
                    display:flex; align-items:center; justify-content:center;
                    font-weight:700; color:white; font-size:0.9rem; flex-shrink:0;">
                    {name[0].upper() if name else 'U'}
                </div>
                <div style="min-width:0;">
                    <div style="font-weight:600; color:#E2E8F0; font-size:0.9rem;
                        white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                        {name}</div>
                    <div style="color:#64748B; font-size:0.72rem; margin-top:0.1rem;">
                        {role.upper()}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Navigation ────────────────────────────────────────
        nav_items = [
            ("📊", "dashboard",     "Dashboard"),
            ("📤", "upload",        "Upload Resume"),
            ("⚡", "analyze",       "Analyze Resume"),
            ("📚", "history",       "Analysis History"),
            ("📝", "cover_letter",  "Cover Letter"),
            ("🎯", "interview_prep","Interview Prep"),
        ]

        if is_admin():
            nav_items.append(("⚙️", "admin", "Admin Panel"))

        current = st.session_state.get("current_page", "dashboard")

        for icon, page_key, label in nav_items:
            is_current = current == page_key
            btn_style = """background:rgba(108,99,255,0.15);border:1px solid rgba(108,99,255,0.3);""" \
                       if is_current else "background:transparent; border:1px solid transparent;"

            if st.button(
                f"{icon}  {label}",
                key=f"nav_{page_key}",
                use_container_width=True,
            ):
                st.session_state.current_page = page_key
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<hr style="border:none;border-top:1px solid #2D2D4E;">', unsafe_allow_html=True)

        # ── Logout ────────────────────────────────────────────
        if st.button("🚪 Sign Out", use_container_width=True, key="nav_logout"):
            clear_session()
            st.rerun()

        # ── Version ───────────────────────────────────────────
        st.markdown("""
        <div style="text-align:center; color:#374151; font-size:0.72rem; margin-top:1rem;">
            v1.0.0 &nbsp;·&nbsp; AI Resume Analyzer
        </div>
        """, unsafe_allow_html=True)


def route_page():
    """Route to the correct page based on session state."""
    page = st.session_state.get("current_page", "dashboard")

    if page == "dashboard":
        from frontend.views import dashboard
        dashboard.show()
    elif page == "upload":
        from frontend.views import upload
        upload.show()
    elif page == "analyze":
        from frontend.views import analyze
        analyze.show()
    elif page == "history":
        from frontend.views import history
        history.show()
    elif page == "cover_letter":
        from frontend.views import cover_letter
        cover_letter.show()
    elif page == "interview_prep":
        from frontend.views import interview_prep
        interview_prep.show()
    elif page == "admin":
        from frontend.views import admin
        admin.show()
    else:
        from frontend.views import dashboard
        dashboard.show()


def main():
    """Main application entry point."""
    # 1. Load custom CSS
    load_css()

    # 2. Initialize session state
    init_session()

    # 3. Show login page if not authenticated
    if not is_logged_in():
        from frontend.views import login
        login.show()
        return

    # 4. Render sidebar navigation
    render_sidebar()

    # 5. Route to the correct page
    route_page()


if __name__ == "__main__":
    main()
