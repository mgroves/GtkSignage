"""
Server Module

Flask web server for GTK Signage.
Runs in a background thread alongside the GTK display.
Configuration is loaded from INI via signage.config.
"""

from __future__ import annotations

import logging
import os
import urllib.parse
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    send_file,
    abort,
)
from flask_wtf.csrf import CSRFProtect, CSRFError

from signage.config import load_config
from signage.slidestore import SlideStore
from signage.routes.slides import slides_bp
from signage.routes.auth import auth_bp
from signage.helpers.auth import login_required


logger = logging.getLogger(__name__)
config = load_config()


# ------------------------------------------------------------
# Flask app factory
# ------------------------------------------------------------

def create_app() -> Flask:
    """
    Create and configure the Flask application.
    """
    app = Flask(__name__)

    # ---- Security -------------------------------------------------
    secret_key = config.get("flask", "secret_key", fallback=None)
    if not secret_key:
        raise RuntimeError("Missing [server].secret_key in config")

    app.secret_key = secret_key
    csrf = CSRFProtect(app)

    # ---- Blueprints ----------------------------------------------
    app.register_blueprint(slides_bp)
    app.register_blueprint(auth_bp)

    # ---- HTTPS redirect (optional) -------------------------------
    use_ssl = config.getboolean("flask", "use_ssl", fallback=False)

    if use_ssl:
        @app.before_request
        def redirect_to_https():
            if (
                request.headers.get("X-Forwarded-Proto", "http") == "http"
                and request.url.startswith("http://")
            ):
                return redirect(
                    request.url.replace("http://", "https://", 1),
                    code=301,
                )

    # ---- CSRF error handler --------------------------------------
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        logger.error("CSRF error: %s", e.description)
        return "CSRF token validation failed.", 400

    # ---- Template filters ----------------------------------------
    @app.template_filter("format_ampm")
    def format_ampm(value):
        if not value or str(value).strip() == "":
            return "N/A"
        try:
            if isinstance(value, str):
                dt = datetime.fromisoformat(value.strip())
            elif isinstance(value, datetime):
                dt = value
            else:
                return "N/A"

            if dt in (datetime.min, datetime.max):
                return "N/A"

            return dt.strftime("%-m/%-d/%Y %-I:%M%p").lower()
        except Exception:
            return "N/A"

    # ---- Internal image serving ----------------------------------
    @app.route("/internal-image/<path:encoded_path>")
    @login_required
    def serve_internal_image(encoded_path):
        full_path = urllib.parse.unquote(encoded_path)
        if not full_path.startswith("/"):
            full_path = "/" + full_path

        if not os.path.isfile(full_path):
            return abort(404)

        return send_file(full_path, mimetype="image/*")

    # ---- Health / index ------------------------------------------
    @app.route("/")
    def index():
        return render_template("index.html")

    return app


# ------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------

def run_flask() -> None:
    """
    Start the Flask server using config-defined host/port.
    Intended to be run in a background thread.
    """
    host = config.get("flask", "host", fallback="127.0.0.1")
    port = config.getint("flask", "port", fallback=5000)
    use_ssl = config.getboolean("flask", "use_ssl", fallback=False)

    logger.info("Flask server starting on %s:%s", host, port)

    app = create_app()

    ssl_context = None
    if use_ssl:
        cert = config.get("flask", "cert", fallback=None)
        key = config.get("flask", "key", fallback=None)

        if cert and key and os.path.exists(cert) and os.path.exists(key):
            ssl_context = (cert, key)
        else:
            logger.warning(
                "SSL enabled but cert/key missing; starting without SSL"
            )

    try:
        app.run(
            host=host,
            port=port,
            ssl_context=ssl_context,
            debug=False,
            use_reloader=False,  # critical for threaded GTK
        )
    except OSError as exc:
        logger.error(
            "Failed to start Flask server on %s:%s (%s)",
            host,
            port,
            exc,
        )