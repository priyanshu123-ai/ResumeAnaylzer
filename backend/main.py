"""
main.py — FastAPI Application Entry Point
==========================================
Starts the FastAPI server, registers all routers,
sets up CORS, initializes the database, and creates the admin user.

Run with:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import get_settings
from backend.database.db import init_db, check_db_connection
from backend.routes import auth, resume, analysis, admin
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


# ═══════════════════════════════════════════════════════════════════════════════
# Application Lifespan (startup + shutdown)
# ═══════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Tasks to run at application startup and shutdown.
    Using the modern FastAPI lifespan context manager.
    """
    # ── Startup ───────────────────────────────────────────────
    logger.info(f"[START] Starting {settings.APP_NAME} v{settings.VERSION}")

    # Initialize database tables
    try:
        init_db()
    except Exception as e:
        logger.error(f"[ERR] Database initialization failed: {e}")
        raise

    # Bootstrap admin user if not exists
    _create_admin_user()

    logger.info("[OK] Application startup complete")
    yield

    # ── Shutdown ──────────────────────────────────────────────
    logger.info("[BYE] Application shutting down...")


def _create_admin_user():
    """
    Create the default admin user on first startup.
    Credentials come from environment variables.
    """
    from backend.database.db import SessionLocal
    from backend.database.models import User
    from backend.utils.auth_utils import hash_password

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        if not existing:
            admin_user = User(
                name=settings.ADMIN_NAME,
                email=settings.ADMIN_EMAIL,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                role="admin",
                is_active=True,
                created_at=datetime.utcnow(),
            )
            db.add(admin_user)
            db.commit()
            logger.info(f"[OK] Admin user created: {settings.ADMIN_EMAIL}")
        else:
            logger.info(f"[INFO]  Admin user already exists: {settings.ADMIN_EMAIL}")
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        db.rollback()
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# FastAPI App Instance
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## AI Resume Analyzer API

    A production-grade REST API for intelligent resume analysis.

    ### Features:
    - 🔐 JWT Authentication
    - 📄 PDF/DOCX Resume Parsing
    - 🤖 AI-powered Analysis (Gemini)
    - 📊 ATS Scoring with TF-IDF
    - 🧠 NLP (spaCy + HuggingFace)
    - 📈 Skill Gap Analysis
    - 📝 Cover Letter Generation
    """,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ───────────────────────────────────────────────────────────
# Allows the Streamlit frontend (port 8501) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",       # Streamlit local dev
        "http://frontend:8501",         # Docker service name
        "http://localhost:3000",        # If using React frontend
        "*",                            # For dev — restrict in production!
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# Routers
# ═══════════════════════════════════════════════════════════════════════════════

app.include_router(auth.router)
app.include_router(resume.router)
app.include_router(analysis.router)
app.include_router(admin.router)


# ═══════════════════════════════════════════════════════════════════════════════
# Core Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["Health"])
def root():
    """API root — confirms the service is running."""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    Checks database connectivity.
    """
    db_ok = check_db_connection()
    return JSONResponse(
        status_code=200 if db_ok else 503,
        content={
            "status": "healthy" if db_ok else "degraded",
            "database": "connected" if db_ok else "disconnected",
            "gemini_enabled": settings.gemini_enabled,
        }
    )
