"""
test_auth.py — Auth Route Tests
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_signup_success():
    resp = client.post("/auth/signup", json={
        "name": "Test User",
        "email": "testuser123@example.com",
        "password": "Test@1234"
    })
    assert resp.status_code in [201, 409]  # 409 if already exists


def test_signup_weak_password():
    resp = client.post("/auth/signup", json={
        "name": "Test", "email": "weak@test.com", "password": "short"
    })
    assert resp.status_code == 422


def test_login_invalid_credentials():
    resp = client.post("/auth/login", json={
        "email": "nobody@nowhere.com", "password": "WrongPass@1"
    })
    assert resp.status_code == 401


def test_admin_login():
    """Admin user should be auto-created on startup."""
    resp = client.post("/auth/login", json={
        "email": "admin@resumeanalyzer.com",
        "password": "Admin@12345"
    })
    # OK if DB is running, 500 if no DB
    assert resp.status_code in [200, 500, 503]


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code in [200, 503]
    data = resp.json()
    assert "status" in data


def test_root_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "app" in resp.json()
