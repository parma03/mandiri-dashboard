from flask import render_template, session, redirect, url_for
from flask_mysqldb import MySQL
from functools import wraps
import MySQLdb.cursors

mysql = MySQL()
MySQLdb = MySQLdb


def login_not_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)

    return decorated_function


def is_logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        return redirect(url_for("auth.index"))

    return decorated_function


def is_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "Administrator" in session["role"]:
            return f(*args, **kwargs)
        return render_template("404.html")

    return decorated_function
