import os
from flask import Flask, render_template, request, redirect, session, url_for
from signage.slidestore import SlideStore
from dotenv import load_dotenv

def run_flask():
    print("Flask server starting...")
    load_dotenv()

    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET")

    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/admin")
    def admin():
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return render_template("admin.html", slides=SlideStore.get_active_slides())

    @app.route("/admin/add", methods=["GET"])
    def add_slide_form():
        return render_template("add.html")

    @app.route("/admin/add", methods=["POST"])
    def add_slide():
        new_slide = {
            "source": request.form["source"],
            "duration": int(request.form["duration"]),
            "start": request.form.get("start") or None,
            "end": request.form.get("end") or None,
            "active": True
        }
        SlideStore.add_slide(new_slide)
        return redirect(url_for("admin"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session["logged_in"] = True
                return redirect(url_for("admin"))
            return render_template("login.html", error="Invalid credentials")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    cert_path = os.path.join(os.path.dirname(__file__), "..", "cert.pem")
    key_path = os.path.join(os.path.dirname(__file__), "..", "key.pem")
    ssl_context = (cert_path, key_path) if os.path.exists(cert_path) and os.path.exists(key_path) else None

    app.run(host="0.0.0.0", port=6969, ssl_context=ssl_context)
