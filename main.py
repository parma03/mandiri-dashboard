from datetime import datetime
from flask import Flask, flash, jsonify, request, session, redirect, url_for
from app.config.utils import mysql, MySQLdb
from app.config.routes import (
    dashboard_bp,
    auth_bp,
    settings_bp,
    users_bp,
    groups_bp,
    articles_bp,
    analytics_bp,
)
from app.controller.auth import auth_index
from app.controller.scraping import news_scraper
import json
import threading
import os


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
    CACHE_FILE = "news_cache.json"

    @app.route("/")
    def index():
        return auth_index()

    @app.route("/savefilters", methods=["POST"])
    def save_filters():
        session["daterange"] = request.json.get("daterange")
        session["multiselect"] = request.json.get("multiselect")
        return jsonify({"status": "success"})

    def load_cache():
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as file:
                return json.load(file)
        return {}

    def save_cache(data):
        with open(CACHE_FILE, "w") as file:
            json.dump(data, file)

    @app.route("/datascrape", methods=["POST"])
    def get_news():
        group_names = request.form.getlist("groups[]")
        date_range = request.form.get("daterange")

        start_date_str, end_date_str = date_range.split(" - ")
        try:
            # Try Month Day, Year format
            start_date = datetime.strptime(start_date_str, "%B %d, %Y").date()
            end_date = datetime.strptime(end_date_str, "%B %d, %Y").date()
        except ValueError:
            # Try MM/DD/YYYY format
            start_date = datetime.strptime(start_date_str, "%m/%d/%Y").date()
            end_date = datetime.strptime(end_date_str, "%m/%d/%Y").date()

        cache = load_cache()
        cache_key = f"{group_names}_{start_date}_{end_date}"
        cached_articles = cache.get(cache_key)

        if cached_articles:
            return jsonify({"status": "success", **cached_articles})

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        count_query = """
            SELECT COUNT(*) as count 
            FROM tb_article 
            WHERE date BETWEEN %s AND %s
        """
        count_params = [start_date, end_date]

        if group_names:
            count_query += " AND n_group IN ({})".format(
                ", ".join(["%s"] * len(group_names))
            )
            count_params.extend(group_names)

        cur.execute(count_query, tuple(count_params))
        count_article = cur.fetchone()
        result_count_article = count_article["count"] if count_article else 0

        # Main data query
        query_params = [start_date, end_date]
        query = """
            SELECT * FROM tb_article
            WHERE date BETWEEN %s AND %s
        """

        if group_names:
            query += " AND n_group IN ({})".format(", ".join(["%s"] * len(group_names)))
            query_params.extend(group_names)

        cur.execute(query, tuple(query_params))
        data_articles = cur.fetchall()

        cur.close()

        response = {
            "status": "success",
            "data_articles": data_articles,
            "count_article": result_count_article,
        }

        # Step 3: Trigger scraping in background
        def background_scrape():
            with app.app_context():
                articles = news_scraper.scrape_news(group_names, start_date, end_date)
                count = len(articles)
                cache[cache_key] = {"data_articles": articles, "count_article": count}
                save_cache(cache)

        threading.Thread(target=background_scrape).start()
        return jsonify(response)

    @app.route("/check_cache", methods=["GET"])
    def check_cache():
        try:
            key = request.args.get("key")
            cache = load_cache()
            if key in cache:
                return jsonify({"status": "updated", **cache[key]})
            return jsonify({"status": "not_found"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

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
