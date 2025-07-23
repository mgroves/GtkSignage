"""
GTK Signage Application - Main Entry Point

This script serves as the entry point for the GTK Signage application.
It starts a Flask web server in a background thread for administration
and initializes the GTK window for displaying slides.

The application combines a web-based admin interface with a GTK-based
display that shows slides according to configured settings.
"""

from signage.ui import SignageWindow
from signage.server import run_flask
import gi
import threading
import sys

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

if __name__ == "__main__":
    try:
        # Run Flask in a background daemon thread
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()

        print("Starting GTK...")
        win = SignageWindow()
        Gtk.main()
    except KeyboardInterrupt:
        print("Caught Ctrl+C, shutting down.")
        Gtk.main_quit()
        sys.exit(0)
