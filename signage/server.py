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

    app.run(host="0.0.0.0", port=6969)
