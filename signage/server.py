import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, send_file, abort
from signage.slidestore import SlideStore
from dotenv import load_dotenv
from signage.models import Slide
from datetime import datetime
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

admin_user = os.getenv("ADMIN_USERNAME")
admin_pass = os.getenv("ADMIN_PASSWORD")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

#format date/time
@app.template_filter('format_ampm')
def format_ampm(value):
    if not value:
        return "N/A"
    try:
        if isinstance(value, str):
            dt = datetime.fromisoformat(value)
        elif isinstance(value, datetime):
            dt = value
        else:
            return "N/A"
        return dt.strftime("%-m/%-d/%Y %-I:%M%p").lower()
    except Exception:
        return "N/A"


# Auth helpers
def is_logged_in():
    return session.get("logged_in", False)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated

# show uploaded images to admin
@app.route("/internal-image/<path:encoded_path>")
@login_required
def serve_internal_image(encoded_path):
    import urllib.parse

    full_path = urllib.parse.unquote(encoded_path)

    # Ensure leading slash is restored if missing
    if not full_path.startswith("/"):
        full_path = "/" + full_path

    print(f"[DEBUG] Attempting to serve actual file path: {full_path}")

    if not os.path.isfile(full_path):
        print("[DEBUG] File not found!")
        return abort(404)

    return send_file(full_path, mimetype="image/*")


# Routes
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form["username"] == admin_user and request.form["password"] == admin_pass:
            session["logged_in"] = True
            return redirect(request.args.get("next") or url_for("admin"))
        else:
            error = "Invalid credentials"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin")
@login_required
def admin():
    return render_template("admin.html", slides=SlideStore.get_active_slides())

@app.route("/admin/add", methods=["GET", "POST"])
@login_required
def admin_add():
    if request.method == "POST":
        uploaded_file = request.files.get("file")
        url_input = request.form.get("source", "").strip()
        filename = None

        # Decide which source to use
        if uploaded_file and uploaded_file.filename:
            filename = uploaded_file.filename
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(save_path)
            source = f"file://{os.path.abspath(save_path)}"
        elif url_input:
            source = url_input
        else:
            return "Either a file or URL is required.", 400

        SlideStore.add_slide({
            "source": source,
            "duration": int(request.form["duration"]),
            "start": request.form["start"],
            "end": request.form["end"]
        })
        return redirect(url_for("admin"))

    return render_template("add.html")

@app.route("/admin/edit/<int:index>", methods=["GET", "POST"])
@login_required
def edit_slide(index):
    SlideStore.force_reload()
    slides = SlideStore._slides
    if index < 0 or index >= len(slides):
        return "Slide not found", 404

    if request.method == "POST":
        source = request.form["source"]
        duration = int(request.form["duration"])
        start_str = request.form.get("start")
        end_str = request.form.get("end")

        start = datetime.fromisoformat(start_str) if start_str else None
        end = datetime.fromisoformat(end_str) if end_str else None

        slides[index] = Slide(source=source, duration=duration, start=start, end=end)
        SlideStore.save_slides(slides)
        return redirect(url_for("admin"))

    return render_template("edit.html", slide=slides[index], index=index)

@app.route("/admin/delete/<int:index>")
@login_required
def delete_slide(index):
    slides = SlideStore.get_all_slides()
    if 0 <= index < len(slides):
        del slides[index]
        SlideStore.save_slides(slides)
        SlideStore.force_reload()
    return redirect("/admin")

# Entrypoint
def run_flask():
    print("Flask server starting...")

    cert_path = os.path.join(os.path.dirname(__file__), "..", "cert.pem")
    key_path = os.path.join(os.path.dirname(__file__), "..", "key.pem")
    ssl_context = (cert_path, key_path) if os.path.exists(cert_path) and os.path.exists(key_path) else None

    app.run(host="0.0.0.0", port=6969, ssl_context=ssl_context)
