"""
Server Module

This module provides a Flask web server for the GTK Signage application.
The server runs in a background thread
alongside the GTK display window.
"""
import os
import urllib.parse
from datetime import datetime
from functools import wraps
import logging

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, send_file, abort
from flask import request, redirect
from flask_wtf.csrf import CSRFProtect, CSRFError

from signage.models import Slide
from signage.slidestore import SlideStore
from signage.routes.slides import slides_bp
from signage.routes.auth import auth_bp
from signage.helpers.auth import login_required
from signage.cache import URLCache

load_dotenv()

HOST = os.getenv("FLASK_HOST", "127.0.0.1")
PORT = int(os.getenv("FLASK_PORT", 5000))
USE_SSL = os.getenv("USE_SSL", "false").lower() == "true"

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
csrf = CSRFProtect(app)

# #######################################
# blueprints for various routes and endpoints
app.register_blueprint(slides_bp)
app.register_blueprint(auth_bp)
# #######################################


# Redirect HTTP to HTTPS if enabled
if USE_SSL:
    @app.before_request
    def redirect_to_https():
        if request.headers.get("X-Forwarded-Proto", "http") == "http" and request.url.startswith("http://"):
            return redirect(request.url.replace("http://", "https://", 1), code=301)

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    """
    Handle CSRF errors by logging the error and returning an error message.
    
    Args:
        e (CSRFError): The CSRF error that occurred.
        
    Returns:
        Response: Error message with 400 status code.
    """
    logging.error(f"CSRF error: {e.description}")
    return "CSRF token validation failed. Please try again.", 400

# Template filters
@app.template_filter('format_ampm')
def format_ampm(value):
    """
    Flask template filter to format datetime values in a user-friendly AM/PM format.
    
    Args:
        value (str, datetime, None): The datetime value to format.
            Can be a datetime object, ISO format string, or None.
            
    Returns:
        str: Formatted date/time string in "m/d/yyyy h:MMam/pm" format,
             or "N/A" if the value is invalid or represents a placeholder date.
    """
    if not value or str(value).strip() == "":
        return "N/A"
    try:
        if isinstance(value, str):
            dt = datetime.fromisoformat(value.strip())
        elif isinstance(value, datetime):
            dt = value
        else:
            return "N/A"

        # Filter out placeholder datetime extremes
        if dt == datetime.min or dt == datetime.max:
            return "N/A"

        return dt.strftime("%-m/%-d/%Y %-I:%M%p").lower()
    except Exception:
        return "N/A"


# Image serving routes
@app.route("/internal-image/<path:encoded_path>")
@login_required
def serve_internal_image(encoded_path):
    """
    Serve internal images to authenticated admin users.
    
    This route decodes the URL-encoded path and serves the file if it exists.
    It requires authentication to prevent unauthorized access to local files.
    
    Args:
        encoded_path (str): URL-encoded file path.
        
    Returns:
        Response: The image file response or a 404 error if the file doesn't exist.
    """
    full_path = urllib.parse.unquote(encoded_path)

    # Ensure leading slash is restored if missing
    if not full_path.startswith("/"):
        full_path = "/" + full_path

    logging.debug(f"Attempting to serve actual file path: {full_path}")

    if not os.path.isfile(full_path):
        logging.debug("File not found!")
        return abort(404)

    return send_file(full_path, mimetype="image/*")

@app.route("/cache-cdn")
def cache_cdn():
    """
    Cache a CDN URL locally.
    
    This route is used to cache Bootstrap CSS and JS files locally.
    It takes a URL parameter and uses the URLCache class to cache the file.
    
    Returns:
        Response: JSON response indicating success or failure.
    """
    url = request.args.get('url')
    if not url:
        return {"success": False, "error": "No URL provided"}, 400
    
    # Check if the URL is already cached and not expired
    if URLCache.is_cached(url) and not URLCache.is_cache_expired(url):
        return {"success": True, "cached": True, "message": "URL already cached"}
    
    # Cache the URL
    success = URLCache.cache_url(url)
    return {"success": success, "cached": success, "message": "URL cached" if success else "Failed to cache URL"}

@app.route("/")
def index():
    """
    Render the main index page.
    
    This just shows that the server is running.
    
    Returns:
        Response: Rendered index.html template.
    """
    return render_template("index.html")

# Entrypoint
def run_flask():
    """
    Start the Flask web server.
    
    This function is the entry point for the Flask server component of the application.
    It configures and starts the Flask server with the appropriate host, port, and SSL settings.
    
    The server is typically run in a background thread alongside the GTK window.
    
    SSL is enabled if USE_SSL is set to "true" in the environment variables and
    the certificate files (cert.pem and key.pem) exist.
    """
    logging.info("Flask server starting...")

    ssl_context = None
    if USE_SSL:
        cert_path = os.path.join(os.path.dirname(__file__), "..", "cert.pem")
        key_path = os.path.join(os.path.dirname(__file__), "..", "key.pem")
        if os.path.exists(cert_path) and os.path.exists(key_path):
            ssl_context = (cert_path, key_path)
        else:
            logging.warning("SSL requested but cert.pem or key.pem not found — continuing without SSL.")

    app.run(host=HOST, port=PORT, ssl_context=ssl_context)