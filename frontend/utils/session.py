"""
session.py — Streamlit Session State Management
================================================
Centralized helpers for reading/writing JWT token and user data
from Streamlit's session_state. Also handles logout.
"""

import streamlit as st
from typing import Optional


def init_session():
    """
    Initialize all required session state keys.
    Call this at the top of app.py and each page.
    """
    defaults = {
        "token": None,
        "user_id": None,
        "user_name": None,
        "user_email": None,
        "user_role": None,
        "is_logged_in": False,
        "current_page": "dashboard",
        "selected_resume_id": None,
        "last_report": None,
        "theme": "dark",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def is_logged_in() -> bool:
    """Check if the user is currently authenticated."""
    return bool(st.session_state.get("token") and st.session_state.get("is_logged_in"))


def is_admin() -> bool:
    """Check if the current user has admin role."""
    return st.session_state.get("user_role") == "admin"


def get_token() -> Optional[str]:
    """Return the current JWT token, or None."""
    return st.session_state.get("token")


def get_user_name() -> str:
    """Return the current user's display name."""
    return st.session_state.get("user_name", "User")


def get_user_email() -> str:
    """Return the current user's email."""
    return st.session_state.get("user_email", "")


def set_session(token: str, user_id: int, name: str, email: str, role: str):
    """
    Store authentication data in session after successful login.

    Args:
        token: JWT access token.
        user_id: User database ID.
        name: User's display name.
        email: User's email.
        role: User role ('user' or 'admin').
    """
    st.session_state.token = token
    st.session_state.user_id = user_id
    st.session_state.user_name = name
    st.session_state.user_email = email
    st.session_state.user_role = role
    st.session_state.is_logged_in = True


def clear_session():
    """
    Log out the current user by clearing all session data.
    After calling this, the app should redirect to the login page.
    """
    keys_to_clear = [
        "token", "user_id", "user_name", "user_email",
        "user_role", "is_logged_in", "selected_resume_id", "last_report"
    ]
    for key in keys_to_clear:
        st.session_state[key] = None
    st.session_state.is_logged_in = False


def set_page(page: str):
    """Navigate to a page by updating session state."""
    st.session_state.current_page = page


def get_page() -> str:
    """Return the currently active page name."""
    return st.session_state.get("current_page", "dashboard")


def store_report(report: dict):
    """Cache the latest analysis report in session for fast re-display."""
    st.session_state.last_report = report


def get_stored_report() -> Optional[dict]:
    """Retrieve the cached analysis report."""
    return st.session_state.get("last_report")
