from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from app.config.utils import is_logged_in, login_not_required, mysql, MySQLdb, is_admin
from app.controller.analytic import data_analytic
from app.controller.auth import auth_login, auth_logout
from app.controller.dashboard import dashboard_index
from app.controller.article import data_article
from app.controller.group import group_index
from app.controller.user import admin_index, operator_index, viewer_index

auth_bp = Blueprint("auth", __name__, template_folder="../templates")
dashboard_bp = Blueprint("dashboard", __name__, template_folder="../templates")
settings_bp = Blueprint("setting", __name__, template_folder="../templates")
users_bp = Blueprint("user", __name__, template_folder="../templates/user")
groups_bp = Blueprint("group", __name__, template_folder="../templates")
articles_bp = Blueprint("article", __name__, template_folder="../templates")
analytics_bp = Blueprint("analytic", __name__, template_folder="../templates/analytic")


# auth
@auth_bp.route("/login", methods=["GET", "POST"])
@login_not_required
def index():
    return auth_login()


# dashboard
@dashboard_bp.route("/")
@is_logged_in
def index():
    return dashboard_index()


# user
@users_bp.route("/admin", methods=["GET", "POST"])
@is_logged_in
@is_admin
def admin():
    return admin_index()


@users_bp.route("/operator", methods=["GET", "POST"])
@is_logged_in
@is_admin
def operator():
    return operator_index()


@users_bp.route("/viewer", methods=["GET", "POST"])
@is_logged_in
@is_admin
def viewer():
    return viewer_index()


# group
@groups_bp.route("/", methods=["GET", "POST"])
@is_logged_in
def index():
    return group_index()


# settings
@settings_bp.route("/profile")
@is_logged_in
def profile():
    return render_template("profile.html")


# article
@articles_bp.route("/", methods=["GET", "POST"])
@is_logged_in
def index():
    return data_article()


# analytic
@analytics_bp.route("/")
@is_logged_in
def index():
    return data_analytic()


@auth_bp.route("/logout")
def logout():
    return auth_logout()
