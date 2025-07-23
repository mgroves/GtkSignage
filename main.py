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

import gi
from gi.repository import Gtk

from signage.server import run_flask
from signage.ui import SignageWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

gi.require_version("Gtk", "3.0")

if __name__ == "__main__":
    try:
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
