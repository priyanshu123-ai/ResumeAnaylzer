"""
config.py — Application Configuration
=====================================
Uses Pydantic BaseSettings to load environment variables from .env
All settings are type-validated and available app-wide via get_settings().
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """
    Central application settings.
    Values are loaded from environment variables or a .env file.
    """

    # ── App ──────────────────────────────────────────────────
    APP_NAME: str = "AI Resume Analyzer"
    DEBUG: bool = False
    VERSION: str = "1.0.0"

    # ── Security / JWT ───────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str = "mysql+pymysql://resume_user:resume_pass@localhost:3306/resume_db"

    # ── Google Gemini ─────────────────────────────────────────
    GEMINI_API_KEY: str = ""

    # ── Hugging Face ─────────────────────────────────────────
    SKIP_HF_MODELS: bool = False

    # ── File Upload ──────────────────────────────────────────
    MAX_FILE_SIZE_MB: int = 10
    UPLOAD_DIR: str = "uploads"

    # ── Admin Bootstrap ──────────────────────────────────────
    ADMIN_EMAIL: str = "admin@resumeanalyzer.com"
    ADMIN_PASSWORD: str = "Admin@12345"
    ADMIN_NAME: str = "Super Admin"

    @field_validator("UPLOAD_DIR")
    @classmethod
    def create_upload_dir(cls, v: str) -> str:
        """Auto-create the upload directory if it doesn't exist."""
        os.makedirs(v, exist_ok=True)
        return v

    @property
    def gemini_enabled(self) -> bool:
        """True if a Gemini API key is configured."""
        return bool(self.GEMINI_API_KEY)

    @property
    def max_file_size_bytes(self) -> int:
        """Return max upload size in bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",   # Ignore MYSQL_HOST, MYSQL_PORT, BACKEND_URL etc.
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    Using lru_cache means we only read .env once per process.
    """
    return Settings()
