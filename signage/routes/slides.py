import os
import logging
import json
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, send_file, jsonify
from signage.slidestore import SlideStore
from signage.helpers.auth import login_required
from signage.models import Slide
from signage.cec_control import get_cec_status, cec_power_on, cec_power_off
from signage.system_monitor import get_all_stats

slides_bp = Blueprint("slides", __name__, template_folder="../templates/slides")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@slides_bp.route("/admin/dashboard")
@login_required
def admin_dashboard():
    """
    Render the admin dashboard page with system stats.

    Returns:
        Response: Rendered dashboard.html template with slides summary.
    """
    slides = SlideStore.get_all_slides()
    return render_template("dashboard.html", slides=slides)

@slides_bp.route("/admin")
@login_required
def admin():
    """
    Render the slides management page.

    Returns:
        Response: Rendered admin.html template with all slides.
    """
    slides = SlideStore.get_all_slides()
    return render_template("admin.html", slides=slides)

@slides_bp.route("/admin/cec")
@login_required
def admin_cec():
    """
    Render the CEC control page.

    Returns:
        Response: Rendered cec.html template.
    """
    return render_template("cec.html")

@slides_bp.route("/admin/api/stats")
@login_required
def admin_api_stats():
    """
    API endpoint for system stats.

    Returns:
        Response: JSON with system stats.
    """
    return jsonify(get_all_stats())

@slides_bp.route("/admin/add", methods=["GET", "POST"])
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
            return redirect(url_for("slides.admin"))
        except (ValueError, TypeError) as e:
            logging.error(f"Error adding slide: {e}")
            return str(e), 400

    return render_template("add.html")

@slides_bp.route("/admin/edit/<int:index>", methods=["GET", "POST"])
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
                return redirect(url_for("slides.admin"))
                
            except (ValueError, TypeError) as e:
                logging.error(f"Error creating slide object: {e}")
                return f"Error updating slide: {e}", 400

        except Exception as e:
            logging.error(f"Unexpected error updating slide: {e}")
            return f"Error updating slide: {e}", 500

    return render_template("edit.html", slide=slides[index], index=index)

@slides_bp.route("/admin/delete/<int:index>", methods=["POST"])
@login_required
def delete_slide(index):
    """
    Handle deleting a slide.
    
    Removes the slide at the specified index and redirects to the admin page.
    This route only accepts POST requests to prevent CSRF attacks.
    
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

@slides_bp.route("/admin/cec-status")
@login_required
def admin_cec_status():
    return {"status": get_cec_status()}

@slides_bp.route("/admin/cec-on", methods=["POST"])
@login_required
def admin_cec_on():
    cec_power_on()
    return redirect(url_for("slides.admin_cec"))

@slides_bp.route("/admin/cec-off", methods=["POST"])
@login_required
def admin_cec_off():
    cec_power_off()
    return redirect(url_for("slides.admin_cec"))

@slides_bp.route("/uploads/<filename>")
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