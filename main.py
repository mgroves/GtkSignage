from signage.ui import SignageWindow
from signage.server import run_flask
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import threading

if __name__ == "__main__":
    print("Flask server starting...")
    threading.Thread(target=run_flask, daemon=True).start()

    print("Starting GTK...")
    win = SignageWindow()
    Gtk.main()
