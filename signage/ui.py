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
import urllib.parse

import gi
from dotenv import load_dotenv
from gi.repository import Gtk, WebKit2, GLib

from signage.slidestore import SlideStore
from signage.cache import URLCache

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
        self.webview.connect("load-failed", self.on_load_failed)
        self.add(self.webview)

        self.slide_index = 0
        self.current_slide = None
        self.show_all()
        
        # Track URLs that are currently being cached
        self._caching_urls = set()
        
        # Track the last displayed slide to avoid redundant caching
        self._last_displayed_slide = None

        # Run cache cleanup on startup and then every 6 hours
        self.cleanup_cache()
        GLib.timeout_add_seconds(6 * 60 * 60, self.cleanup_cache)
        
        GLib.timeout_add_seconds(1, self.slide_loop)
    
    def is_url(self, source):
        """
        Check if a source is a URL.
        
        Args:
            source (str): The source to check.
            
        Returns:
            bool: True if the source is a URL, False otherwise.
        """
        parsed = urllib.parse.urlparse(source)
        return parsed.scheme in ('http', 'https')
    
    def ensure_cached(self, url):
        """
        Ensure that a URL is cached.
        
        This method checks if a URL needs to be cached and caches it if necessary.
        It uses a separate thread to avoid blocking the main thread.
        It also tracks which URLs are currently being cached to avoid starting
        multiple caching threads for the same URL.
        
        Args:
            url (str): The URL to cache.
        """
        try:
            # Skip if this URL is already being cached
            if url in self._caching_urls:
                logging.debug(f"URL already being cached, skipping: {url}")
                return
                
            # Check if the URL is already cached and not expired
            if not URLCache.is_cached(url) or URLCache.is_cache_expired(url):
                logging.info(f"Caching URL: {url}")
                # Add to the set of URLs being cached
                self._caching_urls.add(url)
                # Use a separate thread to cache the URL
                import threading
                thread = threading.Thread(target=self._cache_url_thread, args=(url,))
                thread.daemon = True  # Thread will exit when main thread exits
                thread.start()
            else:
                logging.debug(f"URL already cached: {url}")
        except Exception as e:
            logging.error(f"Error ensuring URL is cached: {e}")
            
    def _cache_url_thread(self, url):
        """
        Cache a URL in a separate thread.
        
        This method is called from a separate thread to avoid blocking the main thread.
        It removes the URL from the set of URLs being cached when it completes,
        whether it succeeds or fails.
        
        Args:
            url (str): The URL to cache.
        """
        try:
            logging.debug(f"Caching URL in thread: {url}")
            URLCache.cache_url(url)
            logging.debug(f"Finished caching URL in thread: {url}")
        except Exception as e:
            logging.error(f"Error caching URL in thread: {url}, {e}")
        finally:
            # Remove the URL from the set of URLs being cached
            if url in self._caching_urls:
                self._caching_urls.remove(url)
    
    def cleanup_cache(self):
        """
        Clean up expired cache files.
        
        This method removes all cached files that are older than the expiry time.
        
        Returns:
            bool: Always returns True to ensure the timeout is repeated.
        """
        logging.info("Running cache cleanup")
        try:
            URLCache.cleanup_expired_cache()
        except Exception as e:
            logging.error(f"Error cleaning up cache: {e}")
        return True
    
    def on_load_failed(self, webview, event, uri, error):
        """
        Handle load failures by falling back to cached content.
        
        This method is called when a web page fails to load. It attempts to
        load the cached version of the page instead.
        
        Args:
            webview (WebKit2.WebView): The webview that failed to load.
            event: The load event.
            uri (str): The URI that failed to load.
            error: The error that occurred.
            
        Returns:
            bool: True to stop the error from propagating, False otherwise.
        """
        logging.error(f"Failed to load {uri}: {error}")
        
        if self.current_slide and self.is_url(self.current_slide.source):
            cached_url = URLCache.get_cached_url(self.current_slide.source)
            if cached_url != self.current_slide.source:
                logging.info(f"Falling back to cached version: {cached_url}")
                webview.load_uri(cached_url)
                return True
        
        return False

    def slide_loop(self):
        """
        Main loop for displaying slides.
        
        This method is called repeatedly to cycle through the active slides.
        If no slides are active, it displays a message prompting the user to
        visit the admin console. Otherwise, it displays each slide for its
        configured duration before moving to the next one.
        
        For URL slides, this method ensures that the content is cached locally
        before displaying it. If the URL cannot be loaded (e.g., due to network
        issues), the cached version is displayed instead.
        
        Returns:
            bool: Always returns False to indicate that the timeout should not
                  be automatically repeated. Instead, a new timeout is scheduled
                  with the appropriate delay for the next slide.
        """
        active_slides = SlideStore.get_active_slides()

        if not active_slides:
            logging.info("No active slides")
            self.slide_index = 0
            self.current_slide = None
            self._last_displayed_slide = None

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
        self.current_slide = active_slides[self.slide_index]
        source = self.current_slide.source
        
        # Check if we're displaying the same slide as before
        same_slide = (self._last_displayed_slide is not None and 
                     self.current_slide.source == self._last_displayed_slide.source)
        
        # Update the last displayed slide
        self._last_displayed_slide = self.current_slide
        
        # Log the slide we're showing
        logging.info(f"Showing slide: {source}")
        
        # Handle URL slides with caching
        if self.is_url(source):
            try:
                # Only start caching if this is a new slide or if caching previously failed
                if not same_slide or not URLCache.is_cached(source):
                    # Start caching the URL in the background, but don't wait for it to complete
                    self.ensure_cached(source)
                
                # Try to load the original URL first
                self.webview.load_uri(source)
                
                # Note: The caching happens in a separate thread, so it won't block the slide loop
                # If the URL can't be loaded, the on_load_failed handler will try to use the cached version
            except Exception as e:
                logging.error(f"Error loading URL {source}: {e}")
                
                # Fall back to cached version if available
                cached_url = URLCache.get_cached_url(source)
                if cached_url != source:
                    logging.info(f"Falling back to cached version: {cached_url}")
                    self.webview.load_uri(cached_url)
                else:
                    logging.error(f"No cached version available for {source}")
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
                                </style>
                            </head>
                            <body>
                                <h1>Error Loading Content</h1>
                                <p>Could not load: {source}</p>
                                <p>No cached version available.</p>
                            </body>
                        </html>
                        """,
                        "about:blank"
                    )
        else:
            # Non-URL slides (e.g., local files) are loaded directly
            self.webview.load_uri(source)

        delay = self.current_slide.duration
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
