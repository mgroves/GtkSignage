import gi
import sys
import os
from gi.repository import Gtk, WebKit2, GLib
from signage.models import Slide
from signage.slidestore import SlideStore
from dotenv import load_dotenv

load_dotenv()

# Read host/port from .env
HOST = os.getenv("FLASK_HOST", "127.0.0.1")
PORT = os.getenv("FLASK_PORT", "5000")

# Normalize localhost for display
DISPLAY_HOST = "localhost" if HOST in ["0.0.0.0", "127.0.0.1"] else HOST
ADMIN_URL = f"http://{DISPLAY_HOST}:{PORT}/admin"

class SignageWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Signage")
        self.set_default_size(1280, 720)
        self.connect("destroy", self.on_destroy)

        self.webview = WebKit2.WebView()
        self.add(self.webview)

        self.slide_index = 0
        self.show_all()

        GLib.timeout_add_seconds(1, self.slide_loop)

    def slide_loop(self):
        active_slides = SlideStore.get_active_slides()

        if not active_slides:
            print("No active slides")
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
        print(f"Showing slide: {current_slide.source}")
        self.webview.load_uri(current_slide.source)

        delay = current_slide.duration
        self.slide_index = (self.slide_index + 1) % len(active_slides)
        GLib.timeout_add_seconds(delay, self.slide_loop)

        return False

    def on_destroy(self, *args):
        print("GTK window closed. Shutting down.")
        Gtk.main_quit()
        sys.exit(0)
