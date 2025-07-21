from signage.ui import SignageWindow
from signage.server import run_flask
import gi
import threading
import sys

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

if __name__ == "__main__":
    try:
        print("Flask server starting...")
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
