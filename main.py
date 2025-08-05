"""
GTK Signage Application - Main Entry Point

This script serves as the entry point for the GTK Signage application.
It starts a Flask web server in a background thread for administration
and initializes the GTK window for displaying slides.

The application combines a web-based admin interface with a GTK-based
display that shows slides according to configured settings.
"""

import sys
import threading
import logging
import os
import time

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from signage.server import run_flask
from signage.ui import SignageWindow
from signage.cec_watchdog import ensure_cec_on_if_needed
from logging.handlers import RotatingFileHandler

# Configure root logger to output to stderr only
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Log format
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Console handler (stderr)
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

# log to file, keep it from getting too big
log_file = os.getenv("LOG_FILE", "gtk_signage.log")  # Default to current dir
max_bytes = int(os.getenv("LOG_MAX_BYTES", 10_485_760))  # 10 MB max size
backup_count = int(os.getenv("LOG_BACKUP_COUNT", 3))    # Keep 3 backups

file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)

# Set log level from environment variable if available
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
if log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
    logger.setLevel(getattr(logging, log_level))

logging.info(f"Logging initialized at {log_level} level")

def run_cec_watchdog():
    while True:
        try:
            ensure_cec_on_if_needed()
            time.sleep(300)  # Check every five minutes
        except Exception as e:
            logging.error(f"CEC watchdog error: {e}")

if __name__ == "__main__":
    try:
        # Start CEC watchdog thread
        cec_thread = threading.Thread(target=run_cec_watchdog, daemon=True)
        cec_thread.start()

        # Run Flask in a background daemon thread
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()

        logging.info("Starting GTK...")
        win = SignageWindow()
        Gtk.main()
    except KeyboardInterrupt:
        logging.info("Caught Ctrl+C, shutting down.")
        Gtk.main_quit()
        sys.exit(0)
