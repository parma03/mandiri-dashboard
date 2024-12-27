from datetime import datetime
from flask import Flask, jsonify, request, session, redirect, url_for
from app.config.utils import mysql, MySQLdb
from app.config.routes import (
    dashboard_bp,
    auth_bp,
    settings_bp,
    users_bp,
    groups_bp,
    articles_bp,
    analytics_bp,
    scraping_bp,
)
from app.controller.auth import auth_index


def create_app():
    app = Flask(__name__, static_folder="app/static", static_url_path="/static")

    app.config["MYSQL_HOST"] = "localhost"
    app.config["MYSQL_USER"] = "root"
    app.config["MYSQL_PASSWORD"] = ""
    app.config["MYSQL_DB"] = "db_dashboard"
    app.secret_key = "8056174bos805"

    mysql.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(settings_bp, url_prefix="/setting")
    app.register_blueprint(users_bp, url_prefix="/user")
    app.register_blueprint(groups_bp, url_prefix="/group")
    app.register_blueprint(articles_bp, url_prefix="/article")
    app.register_blueprint(analytics_bp, url_prefix="/analytic")
    app.register_blueprint(scraping_bp, url_prefix="/scraping")

    @app.route("/")
    def index():
        return auth_index()

    @app.route("/save_filters", methods=["POST"])
    def save_filters():
        session["daterange"] = request.json.get("daterange")
        session["multiselect"] = request.json.get("multiselect")
        return jsonify({"status": "success"})

    @app.route("/datascrape", methods=["POST"])
    def get_news():
        group_names = request.form.getlist("groups[]")
        date_range = request.form.get("daterange")

        start_date_str, end_date_str = date_range.split(" - ")
        start_date = datetime.strptime(start_date_str, "%B %d, %Y").date()
        end_date = datetime.strptime(end_date_str, "%B %d, %Y").date()

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(
            """
            SELECT COUNT(*) as count 
            FROM tb_article 
            WHERE date BETWEEN %s AND %s
            """,
            (start_date, end_date),
        )
        count_article = cur.fetchone()
        result_count_article = count_article["count"] if count_article else 0

        query_params = []
        query = """
            SELECT * FROM tb_article
            WHERE 1=1
        """

        if date_range:
            query += " AND date BETWEEN %s AND %s"
            query_params.extend([start_date, end_date])

        if group_names:
            group_placeholders = ", ".join(["%s"] * len(group_names))
            query += f" AND n_group IN ({group_placeholders})"
            query_params.extend(group_names)
        cur.execute(query, tuple(query_params))
        data_articles = cur.fetchall()

        cur.close()

        return jsonify(
            {
                "status": "success",
                "count_article": result_count_article,
                "data_articles": data_articles,
            }
        )

    @app.context_processor
    def inject_global():
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM tb_group")
        groups = cur.fetchall()
        cur.close()
        return dict(groups=groups)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)