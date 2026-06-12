#!/usr/bin/env python3
"""
MACH-1 v3 — Main Entry Point
ONE master process that runs the CEO agent + scheduler.
The Flask dashboard runs as a separate systemd service.
"""
import sys
import time
import signal
import threading
from datetime import datetime

from config import settings
from utils.logger import get_logger
from utils.database import db
from agents.ceo import CEOAgent
from agents.rss_scraper import init_default_sources
from utils.notify import notify

log = get_logger("mach1.main")

# Global flag for clean shutdown
_shutdown = threading.Event()


def signal_handler(sig, frame):
    log.info("Shutdown signal received")
    _shutdown.set()


def run_scheduled_tasks(ceo: CEOAgent):
    """Background thread: runs health check and backup on schedule."""
    log.info("Scheduler started")

    while not _shutdown.is_set():
        now = datetime.now()

        # Health check at configured time
        if (now.hour == settings.HEALTH_CHECK_HOUR and
                now.minute == settings.HEALTH_CHECK_MINUTE):
            log.info("Running scheduled health check")
            try:
                ceo.devops.run_task({"type": "health_check"})
            except Exception as e:
                log.error(f"Health check failed: {e}")

        # Backup at configured time
        if (now.hour == settings.BACKUP_HOUR and
                now.minute == settings.BACKUP_MINUTE):
            log.info("Running scheduled backup")
            try:
                ceo.devops.run_task({"type": "backup"})
            except Exception as e:
                log.error(f"Backup failed: {e}")

        # Sleep 60 seconds between checks
        _shutdown.wait(60)


def main():
    log.info("=" * 50)
    log.info("MACH-1 v3 starting up")
    log.info(f"Home: {settings.MACH1_HOME}")
    log.info(f"Database: {settings.DB_PATH}")
    log.info("=" * 50)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize
    init_default_sources()
    ceo = CEOAgent()

    # Log startup health
    try:
        result = ceo.devops.run_task({"type": "health_check"})
        log.info("Startup health check complete")
    except Exception as e:
        log.warning(f"Startup health check failed: {e}")

    notify("health_report", "MACH-1 Started", "System is online and ready.")

    # Start scheduler thread
    scheduler = threading.Thread(target=run_scheduled_tasks, args=(ceo,), daemon=True)
    scheduler.start()

    log.info("MACH-1 is running. Dashboard at http://localhost:{settings.FLASK_PORT}")
    log.info("Press Ctrl+C to stop.")

    # Main loop — just keeps the process alive
    # All work happens via dashboard API calls or scheduled tasks
    while not _shutdown.is_set():
        _shutdown.wait(1)

    log.info("MACH-1 shutting down gracefully")
    notify("health_report", "MACH-1 Stopped", "System shut down cleanly.")


if __name__ == "__main__":
    main()
