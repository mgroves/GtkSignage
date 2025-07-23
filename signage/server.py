"""
Server Module

This module provides a Flask web server for the GTK Signage application.
It handles the admin interface for managing slides, including authentication,
slide creation, editing, and deletion. The server runs in a background thread
alongside the GTK display window.
"""
import os
import urllib.parse
from datetime import datetime
from functools import wraps
import logging

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, send_file, abort

from signage.models import Slide
from signage.slidestore import SlideStore

load_dotenv()

HOST = os.getenv("FLASK_HOST", "127.0.0.1")
PORT = int(os.getenv("FLASK_PORT", 5000))
USE_SSL = os.getenv("USE_SSL", "false").lower() == "true"

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

admin_user = os.getenv("ADMIN_USERNAME")
admin_pass = os.getenv("ADMIN_PASSWORD")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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


# Auth helpers
def is_logged_in():
    """
    Check if the current user is logged in.
    
    Returns:
        bool: True if the user is logged in, False otherwise.
    """
    return session.get("logged_in", False)

def login_required(f):
    """
    Decorator to require login for accessing a route.
    
    If the user is not logged in, they will be redirected to the login page.
    The current path will be preserved as the 'next' parameter for redirect after login.
    
    Args:
        f (function): The route function to decorate.
        
    Returns:
        function: The decorated function that checks for login before executing the route.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated

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

@app.route("/uploads/<filename>")
def serve_upload(filename):
    """
    Serve uploaded files publicly.
    
    This route serves files from the uploads directory without requiring authentication.
    It is used for slides that need to be publicly accessible.
    
    Args:
        filename (str): The filename of the uploaded file.
        
    Returns:
        Response: The file response or a 404 error if the file doesn't exist.
    """
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if not os.path.isfile(file_path):
        logging.debug(f"Uploaded file not found: {file_path}")
        return abort(404)
    
    return send_file(file_path)


# Authentication routes
@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user login.
    
    GET: Display the login form.
    POST: Process the login form submission and authenticate the user.
    
    Returns:
        Response: Redirect to admin page on successful login or render login template with error.
    """
    error = None
    if request.method == "POST":
        # Validate form inputs
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        if not username:
            error = "Username is required"
        elif not password:
            error = "Password is required"
        elif username == admin_user and password == admin_pass:
            session["logged_in"] = True
            logging.info(f"Successful login for user: {username}")
            return redirect(request.args.get("next") or url_for("admin"))
        else:
            logging.warning(f"Failed login attempt for user: {username}")
            error = "Invalid credentials"
    
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    """
    Handle user logout.
    
    Removes the logged_in flag from the session and redirects to the login page.
    
    Returns:
        Response: Redirect to login page.
    """
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route("/")
def index():
    """
    Render the main index page.
    
    This is the public-facing page that displays the slides.
    
    Returns:
        Response: Rendered index.html template.
    """
    return render_template("index.html")

@app.route("/admin")
@login_required
def admin():
    """
    Render the admin dashboard page.
    
    This page displays all slides and provides controls for managing them.
    Requires authentication.
    
    Returns:
        Response: Rendered admin.html template with all slides.
    """
    return render_template("admin.html", slides=SlideStore.get_all_slides())

@app.route("/admin/add", methods=["GET", "POST"])
@login_required
def admin_add():
    """
    Handle adding a new slide.
    
    GET: Display the add slide form.
    POST: Process the form submission and add a new slide.
    
    The slide source can be either an uploaded file or a URL.
    
    Returns:
        Response: Redirect to admin page on successful addition or error message.
    """
    if request.method == "POST":
        # Get form inputs
        uploaded_file = request.files.get("file")
        url_input = request.form.get("source", "").strip()
        duration_input = request.form.get("duration", "").strip()
        start_input = request.form.get("start", "").strip()
        end_input = request.form.get("end", "").strip()
        hide = bool(request.form.get("hide"))
        
        # Validate source (either file or URL)
        if uploaded_file and uploaded_file.filename and url_input:
            return "Please provide either a file or URL, not both.", 400
        
        if not uploaded_file or not uploaded_file.filename:
            if not url_input:
                return "Either a file or URL is required.", 400
            
            # Validate URL format
            if not (url_input.startswith('http://') or url_input.startswith('https://')):
                return "URL must start with http:// or https://", 400
            
            source = url_input
        else:
            # Validate file upload
            filename = uploaded_file.filename
            
            # Check file extension
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg', 'webp'}
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            if file_ext not in allowed_extensions:
                return f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}", 400
            
            # Check file size (limit to 10MB)
            max_size = 10 * 1024 * 1024  # 10MB in bytes
            uploaded_file.seek(0, os.SEEK_END)
            file_size = uploaded_file.tell()
            uploaded_file.seek(0)  # Reset file pointer
            
            if file_size > max_size:
                return f"File too large. Maximum size is 10MB.", 400
            
            # Save file
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(save_path)
            
            # Create a URL for the uploaded file using the serve_upload route
            # Use request.host_url to get the base URL (including scheme, host, and port)
            source = f"{request.host_url.rstrip('/')}{ url_for('serve_upload', filename=filename) }"
        
        # Validate duration
        try:
            duration = int(duration_input)
            if duration <= 0:
                return "Duration must be a positive number.", 400
        except ValueError:
            return "Duration must be a valid number.", 400
        
        # Validate start and end times
        start = start_input if start_input else None
        end = end_input if end_input else None
        
        # Create slide data
        slide_data = {
            "source": source,
            "duration": duration,
            "start": start,
            "end": end,
            "hide": hide
        }
        
        try:
            SlideStore.add_slide(slide_data)
            logging.info(f"Added new slide with source: {source}")
            return redirect(url_for("admin"))
        except (ValueError, TypeError) as e:
            logging.error(f"Error adding slide: {e}")
            return str(e), 400

    return render_template("add.html")

@app.route("/admin/edit/<int:index>", methods=["GET", "POST"])
@login_required
def edit_slide(index):
    """
    Handle editing an existing slide.
    
    GET: Display the edit form for the slide at the specified index.
    POST: Process the form submission and update the slide.
    
    Args:
        index (int): The index of the slide to edit.
        
    Returns:
        Response: Redirect to admin page on successful update, error message,
                 or rendered edit.html template.
    """
    slides = SlideStore.get_all_slides()  # Use the getter method, not the private _slides

    if index < 0 or index >= len(slides):
        return "Slide not found", 404

    if request.method == "POST":
        try:
            # Get form inputs
            source = request.form.get("source", "").strip()
            duration_input = request.form.get("duration", "").strip()
            start_str = request.form.get("start", "").strip()
            end_str = request.form.get("end", "").strip()
            hide = "hide" in request.form
            
            # Handle file:// URLs (convert to HTTP/HTTPS URLs)
            if source.startswith('file://'):
                file_path = source[7:]
                if os.path.isfile(file_path):
                    # Extract the filename from the path
                    filename = os.path.basename(file_path)
                    
                    # Check if the file is in the UPLOAD_FOLDER
                    if os.path.dirname(os.path.abspath(file_path)) == os.path.abspath(UPLOAD_FOLDER):
                        # Create a URL for the file using the serve_upload route
                        source = f"{request.host_url.rstrip('/')}{ url_for('serve_upload', filename=filename) }"
                        logging.info(f"Converted file:// URL to HTTP/HTTPS URL: {source}")
                    else:
                        # File is not in the UPLOAD_FOLDER, copy it there
                        import shutil
                        try:
                            shutil.copy2(file_path, os.path.join(UPLOAD_FOLDER, filename))
                            source = f"{request.host_url.rstrip('/')}{ url_for('serve_upload', filename=filename) }"
                            logging.info(f"Copied file to UPLOAD_FOLDER and converted to HTTP/HTTPS URL: {source}")
                        except Exception as e:
                            logging.error(f"Error copying file to UPLOAD_FOLDER: {e}")
                            return f"Error processing file: {e}", 400
                else:
                    return f"File not found: {file_path}", 400
            
            # Validate source
            if not source:
                return "Source is required.", 400
                
            # Validate URL format
            if source.startswith('http://') or source.startswith('https://'):
                # Additional URL validation could be added here if needed
                pass
            else:
                return "Source must start with http:// or https://", 400
            
            # Validate duration
            try:
                duration = int(duration_input)
                if duration <= 0:
                    return "Duration must be a positive number.", 400
            except ValueError:
                return "Duration must be a valid number.", 400
            
            # Validate start and end times
            start = None
            end = None
            
            if start_str:
                try:
                    start = datetime.fromisoformat(start_str)
                except ValueError:
                    return "Invalid start time format.", 400
                    
            if end_str:
                try:
                    end = datetime.fromisoformat(end_str)
                except ValueError:
                    return "Invalid end time format.", 400
            
            # Validate start is before end
            if start and end and start >= end:
                return "End time must be after start time.", 400
            
            # Create updated slide
            try:
                updated_slide = Slide(
                    source=source,
                    duration=duration,
                    start=start,
                    end=end,
                    hide=hide
                )
                
                slides[index] = updated_slide
                SlideStore.save_slides(slides)
                logging.info(f"Updated slide at index {index}")
                return redirect(url_for("admin"))
                
            except (ValueError, TypeError) as e:
                logging.error(f"Error creating slide object: {e}")
                return f"Error updating slide: {e}", 400

        except Exception as e:
            logging.error(f"Unexpected error updating slide: {e}")
            return f"Error updating slide: {e}", 500

    return render_template("edit.html", slide=slides[index], index=index)

@app.route("/admin/delete/<int:index>")
@login_required
def delete_slide(index):
    """
    Handle deleting a slide.
    
    Removes the slide at the specified index and redirects to the admin page.
    
    Args:
        index (int): The index of the slide to delete.
        
    Returns:
        Response: Redirect to admin page.
    """
    slides = SlideStore.get_all_slides()
    if 0 <= index < len(slides):
        del slides[index]
        SlideStore.save_slides(slides)
        SlideStore.force_reload()
    return redirect("/admin")

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