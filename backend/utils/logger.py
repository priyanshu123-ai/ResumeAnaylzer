"""
logger.py — Centralized Logging Setup
======================================
Provides a pre-configured logger using Python's built-in logging + Rich.
Import and use in any module: from utils.logger import get_logger
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Try to use Rich for colourful terminal output; fallback to plain logging
try:
    from rich.logging import RichHandler
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# ── Log directory ────────────────────────────────────────────────────────────
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# ── Log filename (daily rotation) ────────────────────────────────────────────
LOG_FILE = LOG_DIR / f"app_{datetime.now().strftime('%Y-%m-%d')}.log"


def get_logger(name: str = "resume_analyzer") -> logging.Logger:
    """
    Return a named logger with both console and file handlers.
    Uses Rich when available; falls back to plain StreamHandler on
    Windows terminals that can't handle Unicode emoji (cp1252).

    Args:
        name: Logger name — usually the module __name__.

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # ── Console Handler ───────────────────────────────────────
    # Detect Windows terminals with limited encoding (cp1252 etc.)
    import io
    stdout_encoding = getattr(sys.stdout, "encoding", "utf-8") or "utf-8"
    use_rich = RICH_AVAILABLE and stdout_encoding.lower().replace("-", "") in ("utf8", "utf16", "utf32")

    if use_rich:
        try:
            from rich.console import Console
            console_handler = RichHandler(
                console=Console(stderr=False, force_terminal=True),
                rich_tracebacks=True,
                show_path=False,
                markup=False,   # Disable markup to avoid emoji encode errors
            )
        except Exception:
            use_rich = False

    if not use_rich:
        # Safe plain handler — strips emoji automatically
        console_handler = logging.StreamHandler(sys.stdout)

    console_handler.setLevel(logging.INFO)
    fmt = "%(message)s" if use_rich else "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
    console_handler.setFormatter(logging.Formatter(fmt))

    # ── File Handler (DEBUG level — captures everything) ──────
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s — %(name)s:%(lineno)d — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Module-level default logger
logger = get_logger("resume_analyzer")
