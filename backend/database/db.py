"""
db.py — Database Connection & Session Management
==================================================
Sets up SQLAlchemy engine, session factory, and a FastAPI
dependency (get_db) for injecting database sessions into routes.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# ── Create SQLAlchemy engine ──────────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    # Connection pool settings — important for production
    pool_pre_ping=True,        # Test connections before using them
    pool_recycle=3600,         # Recycle connections every hour
    pool_size=10,              # Number of persistent connections
    max_overflow=20,           # Extra connections beyond pool_size
    echo=settings.DEBUG,       # Log SQL queries in debug mode
)

# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,    # We manage transactions manually
    autoflush=False,
    bind=engine
)

# ── Base class for all ORM models ─────────────────────────────────────────────
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    The session is automatically closed after the request finishes.

    Usage in a route:
        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    Create all tables defined in ORM models.
    Called once on application startup.

    Note: For production migrations, use Alembic instead.
    """
    try:
        # Import all models so Base knows about them
        from backend.database import models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        logger.info("[OK] Database tables created/verified successfully.")
    except Exception as e:
        logger.error(f"[ERR] Failed to initialize database: {e}", exc_info=True)
        raise


def check_db_connection() -> bool:
    """
    Ping the database to verify connectivity.
    Used in the /health endpoint.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False
