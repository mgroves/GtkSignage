import logging

from flask import Blueprint, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
from signage.config import get_str

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")

load_dotenv()

admin_user = get_str("auth", "admin_username")
admin_pass = get_str("auth", "admin_password_hash")

@auth_bp.route("/login", methods=["GET", "POST"])
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
        # Verify with password hash
        elif username == admin_user and check_password_hash(admin_pass, password):
            session["logged_in"] = True
            logging.info(f"Successful login for user: {username}")
            
            return redirect(request.args.get("next") or url_for("slides.admin"))
        else:
            logging.warning(f"Failed login attempt for user: {username}")
            error = f"Invalid credentials"
    
    return render_template("login.html", error=error)

@auth_bp.route("/logout")
def logout():
    """
    Handle user logout.
    
    Removes the logged_in flag from the session and redirects to the login page.
    
    Returns:
        Response: Redirect to login page.
    """
    session.pop("logged_in", None)
    return redirect(url_for("auth.login"))