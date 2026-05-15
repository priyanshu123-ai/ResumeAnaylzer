"""
api_client.py — HTTP Client for Backend API
=============================================
Wraps all HTTP requests to the FastAPI backend.
Handles authentication headers and error responses centrally.
"""

import requests
from typing import Any, Dict, Optional, Tuple
import streamlit as st

from frontend.utils.session import get_token, clear_session

# Backend base URL — set via environment variable
import os
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


class APIError(Exception):
    """Raised when the backend returns an error response."""
    def __init__(self, message: str, status_code: int = 0):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _headers(token: Optional[str] = None) -> Dict[str, str]:
    """Build authorization headers."""
    t = token or get_token()
    headers = {"Content-Type": "application/json"}
    if t:
        headers["Authorization"] = f"Bearer {t}"
    return headers


def _handle_response(response: requests.Response) -> Dict:
    """
    Parse a response, raising APIError on non-2xx status.

    Args:
        response: The HTTP response object.

    Returns:
        Parsed JSON dict.

    Raises:
        APIError on HTTP errors.
    """
    if response.status_code == 401:
        # Token expired — clear session and redirect to login
        clear_session()
        st.rerun()

    if not response.ok:
        try:
            detail = response.json().get("detail", "An error occurred.")
        except Exception:
            detail = response.text or "Unknown error."
        raise APIError(detail, response.status_code)

    try:
        return response.json()
    except Exception:
        return {"message": response.text}


def get(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """GET request to the backend."""
    url = f"{BACKEND_URL}{endpoint}"
    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=30)
        return _handle_response(resp)
    except requests.exceptions.ConnectionError:
        raise APIError("Cannot connect to backend. Is the server running?")
    except requests.exceptions.Timeout:
        raise APIError("Request timed out. Please try again.")


def post(endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict:
    """POST request to the backend."""
    url = f"{BACKEND_URL}{endpoint}"
    try:
        resp = requests.post(url, headers=_headers(), data=data, json=json, timeout=60)
        return _handle_response(resp)
    except requests.exceptions.ConnectionError:
        raise APIError("Cannot connect to backend. Is the server running?")
    except requests.exceptions.Timeout:
        raise APIError("Request timed out. The analysis may take a moment.")


def post_file(endpoint: str, files: Dict) -> Dict:
    """POST multipart/form-data (file upload)."""
    url = f"{BACKEND_URL}{endpoint}"
    t = get_token()
    headers = {}
    if t:
        headers["Authorization"] = f"Bearer {t}"
    try:
        resp = requests.post(url, headers=headers, files=files, timeout=60)
        return _handle_response(resp)
    except requests.exceptions.ConnectionError:
        raise APIError("Cannot connect to backend. Is the server running?")
    except requests.exceptions.Timeout:
        raise APIError("Upload timed out. Try a smaller file.")


def put(endpoint: str, json: Optional[Dict] = None) -> Dict:
    """PUT request to the backend."""
    url = f"{BACKEND_URL}{endpoint}"
    try:
        resp = requests.put(url, headers=_headers(), json=json, timeout=30)
        return _handle_response(resp)
    except requests.exceptions.ConnectionError:
        raise APIError("Cannot connect to backend. Is the server running?")


def get_bytes(endpoint: str) -> bytes:
    """GET request that returns raw bytes (for PDF download)."""
    url = f"{BACKEND_URL}{endpoint}"
    t = get_token()
    headers = {}
    if t:
        headers["Authorization"] = f"Bearer {t}"
    try:
        resp = requests.get(url, headers=headers, timeout=60)
        if not resp.ok:
            raise APIError(f"Download failed: {resp.status_code}")
        return resp.content
    except requests.exceptions.ConnectionError:
        raise APIError("Cannot connect to backend.")


# ═══════════════════════════════════════════════════════════════════════════════
# Auth API
# ═══════════════════════════════════════════════════════════════════════════════

def signup(name: str, email: str, password: str) -> Dict:
    return post("/auth/signup", json={"name": name, "email": email, "password": password})


def login(email: str, password: str) -> Dict:
    return post("/auth/login", json={"email": email, "password": password})


def get_profile() -> Dict:
    return get("/auth/me")


def update_profile(name: str = None, phone: str = None, location: str = None, bio: str = None) -> Dict:
    data = {}
    if name: data["name"] = name
    if phone: data["phone"] = phone
    if location: data["location"] = location
    if bio: data["bio"] = bio
    return put("/auth/profile", json=data)


# ═══════════════════════════════════════════════════════════════════════════════
# Resume API
# ═══════════════════════════════════════════════════════════════════════════════

def upload_resume(file_bytes: bytes, filename: str) -> Dict:
    mime = "application/pdf" if filename.lower().endswith(".pdf") else \
           "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    files = {"file": (filename, file_bytes, mime)}
    return post_file("/resume/upload", files)


def list_resumes() -> list:
    return get("/resume/list")


def delete_resume(resume_id: int) -> Dict:
    url = f"{BACKEND_URL}/resume/{resume_id}"
    t = get_token()
    headers = {"Authorization": f"Bearer {t}"}
    resp = requests.delete(url, headers=headers, timeout=30)
    return _handle_response(resp)


# ═══════════════════════════════════════════════════════════════════════════════
# Analysis API
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_resume(resume_id: int, job_description: str, job_title: str, company: str = "") -> Dict:
    return post("/analysis/analyze", json={
        "resume_id": resume_id,
        "job_description": job_description,
        "job_title": job_title,
        "company": company,
    })


def list_reports() -> list:
    return get("/analysis/reports")


def get_report(report_id: int) -> Dict:
    return get(f"/analysis/reports/{report_id}")


def download_report_pdf(report_id: int) -> bytes:
    return get_bytes(f"/analysis/reports/{report_id}/pdf")


def generate_cover_letter(resume_id: int, job_title: str, company: str, jd: str) -> Dict:
    return post("/analysis/cover-letter", json={
        "resume_id": resume_id, "job_title": job_title,
        "company": company, "job_description": jd,
    })


def generate_interview_tips(resume_id: int, job_title: str, jd: str) -> Dict:
    return post("/analysis/interview-tips", json={
        "resume_id": resume_id, "job_title": job_title,
        "job_description": jd,
    })


def compare_resumes(resume_ids: list, jd: str) -> Dict:
    return post("/analysis/compare", json={"resume_ids": resume_ids, "job_description": jd})


def predict_skills(resume_id: int, job_title: str) -> Dict:
    return get("/analysis/skills/predict", params={"resume_id": resume_id, "job_title": job_title})


# ═══════════════════════════════════════════════════════════════════════════════
# Admin API
# ═══════════════════════════════════════════════════════════════════════════════

def admin_list_users() -> list:
    return get("/admin/users")


def admin_list_resumes() -> list:
    return get("/admin/resumes")


def admin_get_analytics() -> Dict:
    return get("/admin/analytics")


def admin_toggle_user(user_id: int) -> Dict:
    url = f"{BACKEND_URL}/admin/users/{user_id}/toggle"
    t = get_token()
    resp = requests.put(url, headers={"Authorization": f"Bearer {t}"}, timeout=30)
    return _handle_response(resp)
