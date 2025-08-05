from functools import wraps
from flask import session, redirect, request, url_for

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
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated