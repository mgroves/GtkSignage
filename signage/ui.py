import gi
import sys
import os
from gi.repository import Gtk, WebKit2, GLib
from signage.models import Slide
from signage.slidestore import SlideStore

class SignageWindow(Gtk.Window):
    def __init__(self):
        # Initialize GTK window with title
        Gtk.Window.__init__(self, title="Signage")
        self.set_default_size(1280, 720)
        self.connect("destroy", self.on_destroy)

        # Create a WebView to show slides (URLs or local files)
        self.webview = WebKit2.WebView()
        self.add(self.webview)

        # Index of the current slide
        self.slide_index = 0

        # Show the window
        self.show_all()

        # Start slide loop after 1 second
        GLib.timeout_add_seconds(1, self.slide_loop)

    def slide_loop(self):
        # Get currently active slides from SlideStore
        active_slides = SlideStore.get_active_slides()

        # If no slides are active, wait and try again
        if not active_slides:
            print("No active slides")
            self.slide_index = 0  # Reset index to avoid out-of-bounds later
            GLib.timeout_add_seconds(5, self.slide_loop)
            return True  # Keep the loop going

        # Ensure index stays within bounds if slide count changes
        self.slide_index = self.slide_index % len(active_slides)

        # Get the current slide and load it in the WebView
        current_slide = active_slides[self.slide_index]
        print(f"Showing slide: {current_slide.source}")
        self.webview.load_uri(current_slide.source)

        # Schedule next slide after current one's duration
        delay = current_slide.duration
        self.slide_index = (self.slide_index + 1) % len(active_slides)
        GLib.timeout_add_seconds(delay, self.slide_loop)

        return False  # Don't repeat immediately; will be called after delay

    def on_destroy(self, *args):
        # Exit cleanly when window is closed
        print("GTK window closed. Shutting down.")
        Gtk.main_quit()
        sys.exit(0)
