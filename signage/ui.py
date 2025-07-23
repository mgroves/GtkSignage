"""
UI Module

This module provides the GTK-based user interface for the signage application.
It creates a window with a WebKit2 webview that displays slides in a loop.
The slides are loaded from the SlideStore and displayed according to their
configured duration.
"""
import os
import sys
import logging

import gi
from dotenv import load_dotenv
from gi.repository import Gtk, WebKit2, GLib

from signage.slidestore import SlideStore

load_dotenv()

# Read host/port from .env
HOST = os.getenv("FLASK_HOST", "127.0.0.1")
PORT = os.getenv("FLASK_PORT", "5000")
USE_SSL = os.getenv("USE_SSL", "false").lower() == "true"

# Normalize localhost for display
DISPLAY_HOST = "localhost" if HOST in ["0.0.0.0", "127.0.0.1"] else HOST
SCHEME = "https" if USE_SSL else "http"
ADMIN_URL = f"{SCHEME}://{DISPLAY_HOST}:{PORT}/admin"

class SignageWindow(Gtk.Window):
    """
    Main window for the GTK Signage application.
    
    This class creates a GTK window with a WebKit2 webview that displays slides
    in a continuous loop. It handles the display logic, including timing between
    slides and showing a message when no slides are available.
    """
    def __init__(self):
        """
        Initialize the SignageWindow.
        
        Creates a GTK window with a WebKit2 webview, sets up the initial size,
        and starts the slide loop after a 1-second delay.
        """
        Gtk.Window.__init__(self, title="Signage")
        self.set_default_size(1280, 720)
        self.connect("destroy", self.on_destroy)

        self.webview = WebKit2.WebView()
        self.add(self.webview)

        self.slide_index = 0
        self.show_all()

        GLib.timeout_add_seconds(1, self.slide_loop)

    def slide_loop(self):
        """
        Main loop for displaying slides.
        
        This method is called repeatedly to cycle through the active slides.
        If no slides are active, it displays a message prompting the user to
        visit the admin console. Otherwise, it displays each slide for its
        configured duration before moving to the next one.
        
        Returns:
            bool: Always returns False to indicate that the timeout should not
                  be automatically repeated. Instead, a new timeout is scheduled
                  with the appropriate delay for the next slide.
        """
        active_slides = SlideStore.get_active_slides()

        if not active_slides:
            logging.info("No active slides")
            self.slide_index = 0

            # Show message prompting user to visit the admin console
            self.webview.load_html(
                f"""
                <html>
                    <head>
                        <style>
                            body {{
                                font-family: sans-serif;
                                text-align: center;
                                margin-top: 20%;
                                color: #444;
                            }}
                            a {{
                                color: #0066cc;
                                text-decoration: none;
                                font-weight: bold;
                            }}
                        </style>
                    </head>
                    <body>
                        <h1>No slides yet</h1>
                        <p>Add some slides in the Admin Console.</p>
                        <p>URL: <b>{ADMIN_URL}</b></p>
                    </body>
                </html>
                """,
                "about:blank"
            )

            GLib.timeout_add_seconds(5, self.slide_loop)
            return False

        self.slide_index %= len(active_slides)
        current_slide = active_slides[self.slide_index]
        logging.info(f"Showing slide: {current_slide.source}")
        self.webview.load_uri(current_slide.source)

        delay = current_slide.duration
        self.slide_index = (self.slide_index + 1) % len(active_slides)
        GLib.timeout_add_seconds(delay, self.slide_loop)

        return False

    def on_destroy(self, *args):
        """
        Handle the window destroy event.
        
        This method is called when the window is closed. It stops the GTK main loop
        and exits the application.
        
        Args:
            *args: Variable length argument list (not used).
        """
        logging.info("GTK window closed. Shutting down.")
        Gtk.main_quit()
        sys.exit(0)
