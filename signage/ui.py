import gi
import sys
import os
from gi.repository import Gtk, WebKit2, GLib
from signage.models import Slide
from signage.slidestore import SlideStore

store = SlideStore()
slides = store.load_slides()

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

    def on_destroy(self, *args):
        print("GTK window closed. Shutting down.")
        Gtk.main_quit()
        sys.exit(0)