"""
MACH-1 Logging
Unified logging for all agents and services.
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

_configured = False


def get_logger(name: str = "mach1") -> logging.Logger:
    """Get a named logger. First call configures root."""
    global _configured
    logger = logging.getLogger(name)

    if not _configured:
        from config import LOG_DIR

        logger.setLevel(logging.DEBUG)

        fmt = logging.Formatter(
            "%(asctime)s | %(name)-18s | %(levelname)-7s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler (INFO+)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(fmt)
        logger.addHandler(ch)

        # File handler (DEBUG+, rotates at 10MB, keep 5)
        log_file = LOG_DIR / "mach1.log"
        fh = RotatingFileHandler(
            log_file, maxBytes=10_000_000, backupCount=5, encoding="utf-8"
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

        _configured = True

    return logger
