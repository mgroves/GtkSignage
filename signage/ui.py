"""
UI Module

GTK-based UI for the signage application.
Displays slides using a WebKit2 WebView in a fullscreen window.
"""

from __future__ import annotations

import sys
import logging
import urllib.parse
import threading

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")

from gi.repository import Gtk, WebKit2, GLib

from signage.config import load_config
from signage.slidestore import SlideStore
from signage.cache import URLCache


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

config = load_config()

FLASK_HOST = config.get("flask", "host", fallback="127.0.0.1")
FLASK_PORT = config.getint("flask", "port", fallback=5000)
USE_SSL = config.getboolean("flask", "use_ssl", fallback=False)

DISPLAY_HOST = "localhost" if FLASK_HOST in ("0.0.0.0", "127.0.0.1") else FLASK_HOST
SCHEME = "https" if USE_SSL else "http"
ADMIN_URL = f"{SCHEME}://{DISPLAY_HOST}:{FLASK_PORT}/admin"

CACHE_CLEANUP_INTERVAL = config.getint(
    "cache", "cleanup_interval_seconds", fallback=6 * 60 * 60
)


# ------------------------------------------------------------
# Window
# ------------------------------------------------------------
class SignageWindow(Gtk.Window):
    """
    Main GTK window that displays signage slides.
    """

    def __init__(self) -> None:
        super().__init__(title="Signage")

        self.set_default_size(1280, 720)
        self.connect("destroy", self.on_destroy)

        # --------------------------------------------------------
        # WebKit WebView (GPU acceleration disabled)
        # --------------------------------------------------------

        self.webview = WebKit2.WebView()

        settings = self.webview.get_settings()
        settings.set_enable_accelerated_2d_canvas(False)
        settings.set_enable_webgl(False)
        settings.set_hardware_acceleration_policy(
            WebKit2.HardwareAccelerationPolicy.NEVER
        )

        self.webview.connect("load-failed", self.on_load_failed)

        # --------------------------------------------------------
        # Layout
        # --------------------------------------------------------

        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.pack_start(self.webview, True, True, 0)
        self.add(container)

        # --------------------------------------------------------
        # Slideshow state
        # --------------------------------------------------------

        self.slide_index = 0
        self.current_slide = None
        self._last_displayed_slide = None
        self._caching_urls: set[str] = set()

        self.show_all()

        # --------------------------------------------------------
        # Cache maintenance
        # --------------------------------------------------------

        self.cleanup_cache()
        GLib.timeout_add_seconds(CACHE_CLEANUP_INTERVAL, self.cleanup_cache)

        # --------------------------------------------------------
        # Start slideshow
        # --------------------------------------------------------

        GLib.timeout_add_seconds(1, self.slide_loop)

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------

    @staticmethod
    def is_url(source: str) -> bool:
        parsed = urllib.parse.urlparse(source)
        return parsed.scheme in ("http", "https")

    def ensure_cached(self, url: str) -> None:
        if url in self._caching_urls:
            return

        if URLCache.is_cached(url) and not URLCache.is_cache_expired(url):
            return

        logging.info("Caching URL: %s", url)
        self._caching_urls.add(url)

        thread = threading.Thread(
            target=self._cache_url_thread,
            args=(url,),
            daemon=True,
        )
        thread.start()

    def _cache_url_thread(self, url: str) -> None:
        try:
            URLCache.cache_url(url)
        except Exception as exc:
            logging.error("Error caching URL %s: %s", url, exc)
        finally:
            self._caching_urls.discard(url)

    def cleanup_cache(self) -> bool:
        logging.info("Running cache cleanup")
        try:
            URLCache.cleanup_expired_cache()
        except Exception as exc:
            logging.error("Cache cleanup error: %s", exc)
        return True

    # --------------------------------------------------------
    # WebKit callbacks
    # --------------------------------------------------------

    def on_load_failed(self, webview, load_event, uri, error) -> bool:
        logging.error("Failed to load %s: %s", uri, error)

        if self.current_slide and self.is_url(self.current_slide.source):
            cached = URLCache.get_cached_url(self.current_slide.source)
            if cached != self.current_slide.source:
                logging.info("Falling back to cached version: %s", cached)
                webview.load_uri(cached)
                return True

        return False

    # --------------------------------------------------------
    # Slideshow
    # --------------------------------------------------------

    def slide_loop(self) -> bool:
        slides = SlideStore.get_active_slides()

        if not slides:
            self._show_no_slides_message()
            return True  # keep the existing timer alive

        self.slide_index %= len(slides)
        self.current_slide = slides[self.slide_index]
        source = self.current_slide.source

        same_slide = (
            self._last_displayed_slide is not None
            and source == self._last_displayed_slide.source
        )
        self._last_displayed_slide = self.current_slide

        logging.info("Showing slide: %s", source)

        if self.is_url(source):
            if not same_slide:
                self.ensure_cached(source)
            self.webview.load_uri(source)
        else:
            self.webview.load_uri(source)

        delay = self.current_slide.duration
        self.slide_index += 1

        GLib.timeout_add_seconds(delay, self.slide_loop)
        return False

    def _show_no_slides_message(self) -> None:
        self.slide_index = 0
        self.current_slide = None
        self._last_displayed_slide = None

        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
            body {{
                font-family: sans-serif;
                text-align: center;
                margin-top: 20%;
                color: #444;
                background: #fff;
            }}
            h1 {{ color: #fff; }}
            p {{ color: #ccc; }}
            </style>
        </head>
        <body>
            <h1>No slides configured</h1>
            <p>Add slides in the admin console:</p>
            <p><b>{ADMIN_URL}</b></p>
        </body>
        </html>
        """

        self.webview.load_html(html, None)

        self.webview.show()
        self.show_all()

    # --------------------------------------------------------
    # Shutdown
    # --------------------------------------------------------

    def on_destroy(self, *_args) -> None:
        logging.info("GTK window closed. Shutting down.")
        Gtk.main_quit()
        sys.exit(0)