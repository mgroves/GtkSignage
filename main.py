#!/usr/bin/env python3
"""
GTK Signage Application - Main Entry Point
"""

from __future__ import annotations

import sys
import threading
import logging
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ------------------------------------------------------------
# GTK / WebKit MUST be set up FIRST, together
# ------------------------------------------------------------

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gtk

# ------------------------------------------------------------
# Now it is safe to import app code that uses GTK/WebKit
# ------------------------------------------------------------

from signage.config import load_config, get_config_path
from signage.server import run_flask
from signage.ui import SignageWindow
from signage.cec_watchdog import ensure_cec_on_if_needed

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

config = load_config()

LOG_LEVEL = config.get("logging", "level", fallback="INFO").upper()
LOG_FILE = config.get("logging", "file", fallback="gtk_signage.log")
LOG_MAX_BYTES = config.getint("logging", "max_bytes", fallback=10_485_760)
LOG_BACKUP_COUNT = config.getint("logging", "backup_count", fallback=3)

# ------------------------------------------------------------
# Logging setup
# ------------------------------------------------------------

logger = logging.getLogger()
logger.setLevel(logging.INFO)

log_format = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

console_handler = logging.StreamHandler(sys.stderr)
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

log_path = Path(LOG_FILE).expanduser()
file_handler = RotatingFileHandler(
    log_path,
    maxBytes=LOG_MAX_BYTES,
    backupCount=LOG_BACKUP_COUNT,
)
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)

if hasattr(logging, LOG_LEVEL):
    logger.setLevel(getattr(logging, LOG_LEVEL))

logging.info("Logging initialized at %s level", LOG_LEVEL)
logging.info("Using config file: %s", get_config_path())

# ------------------------------------------------------------
# Background threads
# ------------------------------------------------------------

def run_cec_watchdog():
    interval = config.getint("cec", "poll_seconds", fallback=300)
    while True:
        try:
            ensure_cec_on_if_needed()
        except Exception as exc:
            logging.error("CEC watchdog error: %s", exc)
        time.sleep(interval)

def start_flask():
    run_flask()

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main() -> None:
    try:
        logging.info("Starting GTK…")

        # GTK window MUST be created before background services
        SignageWindow()

        # Start background services AFTER GTK exists
        threading.Thread(
            target=start_flask,
            daemon=True,
            name="flask-server",
        ).start()

        threading.Thread(
            target=run_cec_watchdog,
            daemon=True,
            name="cec-watchdog",
        ).start()

        Gtk.main()

    except KeyboardInterrupt:
        logging.info("Caught Ctrl+C, shutting down.")
        Gtk.main_quit()
        sys.exit(0)

if __name__ == "__main__":
    main()