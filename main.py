import gi
import threading
from signage.server import run_flask
from signage.ui import SignageWindow
from gi.repository import Gtk

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("Starting GTK...")
    win = SignageWindow()
    Gtk.main()