"""
login.py — Login & Signup Page
================================
Two-tab UI for user authentication.
Handles JWT token storage in session state on success.
"""

import streamlit as st
from frontend.utils.api_client import login, signup, APIError
from frontend.utils.session import set_session
from frontend.components.cards import render_alert


def show():
    """Render the login/signup page."""

    # ── Page Layout ────────────────────────────────────────────
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0F0F1A 0%, #1A1A2E 50%, #16213E 100%) !important; }
    .auth-container {
        max-width: 440px; margin: 0 auto; padding: 2.5rem;
        background: rgba(26,26,46,0.9); border: 1px solid rgba(108,99,255,0.2);
        border-radius: 20px; backdrop-filter: blur(12px);
        box-shadow: 0 20px 60px rgba(108,99,255,0.2);
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Logo / Header ─────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding: 2rem 0 1.5rem;">
        <div style="font-size:3.5rem; margin-bottom:0.75rem;">🤖</div>
        <h1 style="font-family:'Outfit',sans-serif; font-size:2rem;
                   background:linear-gradient(135deg,#6C63FF,#A78BFA);
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                   margin:0 0 0.4rem;">AI Resume Analyzer</h1>
        <p style="color:#64748B; font-size:0.95rem; margin:0;">
            Your AI-powered career co-pilot
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────
    tab_login, tab_signup = st.tabs(["🔑 Sign In", "📝 Create Account"])

    # ──────────────────────── LOGIN TAB ───────────────────────
    with tab_login:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email Address", placeholder="you@example.com",
                                  key="login_email")
            password = st.text_input("Password", type="password",
                                     placeholder="Your password", key="login_pass")
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Sign In →", use_container_width=True)

            if submitted:
                if not email or not password:
                    render_alert("Please fill in all fields.", "warning")
                else:
                    with st.spinner("Signing in..."):
                        try:
                            data = login(email, password)
                            set_session(
                                token=data["access_token"],
                                user_id=data["user_id"],
                                name=data["name"],
                                email=data["email"],
                                role=data["role"],
                            )
                            st.success(f"Welcome back, {data['name']}! 🎉")
                            st.rerun()
                        except APIError as e:
                            render_alert(e.message, "danger")

        st.markdown("""
        <div style="text-align:center; margin-top:1.5rem; color:#64748B; font-size:0.85rem;">
            <b>Demo Admin:</b> admin@resumeanalyzer.com / Admin@12345
        </div>
        """, unsafe_allow_html=True)

    # ──────────────────────── SIGNUP TAB ──────────────────────
    with tab_signup:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("signup_form", clear_on_submit=False):
            name = st.text_input("Full Name", placeholder="John Doe", key="su_name")
            email = st.text_input("Email Address", placeholder="you@example.com", key="su_email")
            password = st.text_input("Password", type="password",
                                     placeholder="Min 8 chars, 1 uppercase, 1 digit",
                                     key="su_pass")
            confirm = st.text_input("Confirm Password", type="password",
                                    placeholder="Repeat password", key="su_confirm")
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Create Account →", use_container_width=True)

            if submitted:
                if not all([name, email, password, confirm]):
                    render_alert("Please fill in all fields.", "warning")
                elif password != confirm:
                    render_alert("Passwords do not match.", "danger")
                else:
                    with st.spinner("Creating your account..."):
                        try:
                            signup(name, email, password)
                            render_alert("Account created! Please sign in.", "success")
                        except APIError as e:
                            render_alert(e.message, "danger")

        st.markdown("""
        <div style="text-align:center; margin-top:1.5rem;">
            <div style="color:#64748B; font-size:0.8rem; line-height:1.6;">
                ✅ Free to use &nbsp;|&nbsp; 🔒 Your data is secure &nbsp;|&nbsp; 🤖 AI-powered
            </div>
        </div>
        """, unsafe_allow_html=True)
