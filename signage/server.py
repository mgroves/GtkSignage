import os
from flask import Flask, render_template

def run_flask():
    print("Flask server starting...")
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/admin")
    def admin():
        return render_template("admin.html")

    # Load SSL certs if available
    cert_path = os.path.join(os.path.dirname(__file__), "..", "cert.pem")
    key_path = os.path.join(os.path.dirname(__file__), "..", "key.pem")
    ssl_context = (cert_path, key_path) if os.path.exists(cert_path) and os.path.exists(key_path) else None

    app.run(host="0.0.0.0", port=6969, ssl_context=ssl_context)
