from flask import Flask

def run_flask():
    print("Flask server starting...")
    app = Flask(__name__)

    @app.route("/")
    def index():
        return "<h1>Signage is running</h1>"

    @app.route("/admin")
    def admin():
        return "<h2>Admin Panel</h2><p>This will allow editing slides.</p>"

    app.run(host="0.0.0.0", port=6969)