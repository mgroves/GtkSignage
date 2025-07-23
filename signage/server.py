import os
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, send_file, abort, Response
from signage.slidestore import SlideStore
from dotenv import load_dotenv
from signage.models import Slide
from datetime import datetime
from functools import wraps

load_dotenv()

HOST: str = os.getenv("FLASK_HOST", "127.0.0.1")
PORT: int = int(os.getenv("FLASK_PORT", 5000))
USE_SSL: bool = os.getenv("USE_SSL", "false").lower() == "true"

app: Flask = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

admin_user: Optional[str] = os.getenv("ADMIN_USERNAME")
admin_pass: Optional[str] = os.getenv("ADMIN_PASSWORD")

UPLOAD_FOLDER: str = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

#format date/time
@app.template_filter('format_ampm')
def format_ampm(value: Union[str, datetime, None]) -> str:
    if not value or str(value).strip() == "":
        return "N/A"
    try:
        if isinstance(value, str):
            dt: datetime = datetime.fromisoformat(value.strip())
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
def is_logged_in() -> bool:
    return session.get("logged_in", False)

F = TypeVar('F', bound=Callable[..., Any])

def login_required(f: F) -> F:
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        if not is_logged_in():
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return cast(F, decorated)

# show uploaded images to admin
@app.route("/internal-image/<path:encoded_path>")
@login_required
def serve_internal_image(encoded_path: str) -> Response:
    import urllib.parse

    full_path: str = urllib.parse.unquote(encoded_path)

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
def login() -> Union[str, Response]:
    error: Optional[str] = None
    if request.method == "POST":
        if request.form["username"] == admin_user and request.form["password"] == admin_pass:
            session["logged_in"] = True
            return redirect(request.args.get("next") or url_for("admin"))
        else:
            error = "Invalid credentials"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout() -> Response:
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route("/")
def index() -> str:
    return render_template("index.html")

@app.route("/admin")
@login_required
def admin() -> str:
    return render_template("admin.html", slides=SlideStore.get_all_slides())

@app.route("/admin/add", methods=["GET", "POST"])
@login_required
def admin_add() -> Union[str, Response, Tuple[str, int]]:
    if request.method == "POST":
        uploaded_file = request.files.get("file")
        url_input: str = request.form.get("source", "").strip()
        hide: bool = bool(request.form.get("hide"))
        filename: Optional[str] = None

        # Decide which source to use
        if uploaded_file and uploaded_file.filename:
            filename = uploaded_file.filename
            save_path: str = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(save_path)
            source: str = f"file://{os.path.abspath(save_path)}"
        elif url_input:
            source = url_input
        else:
            return "Either a file or URL is required.", 400

        SlideStore.add_slide({
            "source": source,
            "duration": int(request.form["duration"]),
            "start": request.form["start"],
            "end": request.form["end"],
            "hide": hide
        })
        return redirect(url_for("admin"))

    return render_template("add.html")

@app.route("/admin/edit/<int:index>", methods=["GET", "POST"])
@login_required
def edit_slide(index: int) -> Union[str, Response, Tuple[str, int]]:
    slides: List[Slide] = SlideStore.get_all_slides()  # Use the getter method, not the private _slides

    if index < 0 or index >= len(slides):
        return "Slide not found", 404

    if request.method == "POST":
        try:
            source: str = request.form["source"]
            duration: int = int(request.form["duration"])
            start_str: Optional[str] = request.form.get("start")
            end_str: Optional[str] = request.form.get("end")
            hide: bool = "hide" in request.form

            start: Optional[datetime] = datetime.fromisoformat(start_str) if start_str else None
            end: Optional[datetime] = datetime.fromisoformat(end_str) if end_str else None

            slides[index] = Slide(
                source=source,
                duration=duration,
                start=start,
                end=end,
                hide=hide
            )

            SlideStore.save_slides(slides)
            return redirect(url_for("admin"))

        except Exception as e:
            return f"Error updating slide: {e}", 400

    return render_template("edit.html", slide=slides[index], index=index)

@app.route("/admin/delete/<int:index>")
@login_required
def delete_slide(index: int) -> Response:
    slides: List[Slide] = SlideStore.get_all_slides()
    if 0 <= index < len(slides):
        del slides[index]
        SlideStore.save_slides(slides)
        SlideStore.force_reload()
    return redirect("/admin")

# Entrypoint
def run_flask() -> None:
    print("Flask server starting...")

    ssl_context: Optional[Tuple[str, str]] = None
    if USE_SSL:
        cert_path: str = os.path.join(os.path.dirname(__file__), "..", "cert.pem")
        key_path: str = os.path.join(os.path.dirname(__file__), "..", "key.pem")
        if os.path.exists(cert_path) and os.path.exists(key_path):
            ssl_context = (cert_path, key_path)
        else:
            print("⚠️ SSL requested but cert.pem or key.pem not found — continuing without SSL.")

    app.run(host=HOST, port=PORT, ssl_context=ssl_context)