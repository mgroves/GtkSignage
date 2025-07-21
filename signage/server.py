import os
from flask import Flask, render_template, request, redirect, url_for, session
from signage.slidestore import SlideStore
from dotenv import load_dotenv

def run_flask():
    print("Flask server starting...")
    app = Flask(__name__)
    load_dotenv()

    app.secret_key = os.getenv("FLASK_SECRET_KEY")
    admin_user = os.getenv("ADMIN_USERNAME")
    admin_pass = os.getenv("ADMIN_PASSWORD")

    def is_logged_in():
        return session.get("logged_in", False)

    def login_required(f):
        from functools import wraps
        @wraps(f)
        def decorated(*args, **kwargs):
            if not is_logged_in():
                return redirect(url_for("login", next=request.path))
            return f(*args, **kwargs)
        return decorated

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
            SlideStore.add_slide({
                "source": request.form["source"],
                "duration": int(request.form["duration"]),
                "start": request.form["start"],
                "end": request.form["end"]
            })
            return redirect(url_for("admin"))
        return render_template("add.html")

    # stubs for edit/delete (add @login_required when implemented)
    @app.route("/admin/edit/<int:index>")
    @login_required
    def admin_edit(index):
        return f"Edit slide {index}"

    @app.route("/admin/delete/<int:index>")
    @login_required
    def admin_delete(index):
        return f"Delete slide {index}"

    cert_path = os.path.join(os.path.dirname(__file__), "..", "cert.pem")
    key_path = os.path.join(os.path.dirname(__file__), "..", "key.pem")
    ssl_context = (cert_path, key_path) if os.path.exists(cert_path) and os.path.exists(key_path) else None

    app.run(host="0.0.0.0", port=6969, ssl_context=ssl_context)
