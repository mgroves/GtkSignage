import gi
gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.0")
from gi.repository import Gtk, WebKit2, GLib
import threading
from flask import Flask
import time
import os
from datetime import datetime

# --- Slide model ---
class Slide:
    def __init__(self, source, duration, start=None, end=None):
        self.source = source
        self.duration = duration
        self.start = start or datetime.min
        self.end = end or datetime.max

    def is_active(self):
        now = datetime.now()
        return self.start <= now <= self.end

slides = [
    Slide("https://grovesmanagementllc.com/menus/screen1", 10),
    Slide("file://" + os.path.abspath("images/test.jpg"), 5)
]

# --- GTK Window ---
class SignageWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Signage")
        self.set_default_size(1280, 720)
        self.connect("destroy", Gtk.main_quit)

        self.webview = WebKit2.WebView()
        self.add(self.webview)

        self.slide_index = 0
        self.show_all()
        GLib.timeout_add_seconds(1, self.slide_loop)

    def slide_loop(self):
        active_slides = [s for s in slides if s.is_active()]
        if not active_slides:
            print("No active slides")
            return True

        slide = active_slides[self.slide_index % len(active_slides)]
        print(f"Showing slide: {slide.source}")
        self.webview.load_uri(slide.source)

        delay = slide.duration
        self.slide_index += 1
        GLib.timeout_add_seconds(delay, self.slide_loop)
        return False

# --- Flask API ---
def run_flask():
    print("Flask server starting...")
    app = Flask(__name__)

    @app.route("/")
    def index():
        return "<h1>Signage is running</h1>"

    @app.route("/admin")
    def admin():
        return "<h2>Admin Panel</h2><p>This will allow editing slides.</p>"

    app.run(host="0.0.0.0", port=6969)

# --- Main ---
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("Starting GTK...")
    win = SignageWindow()
    Gtk.main()
