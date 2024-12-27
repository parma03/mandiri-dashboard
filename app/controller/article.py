from flask import jsonify, render_template, request, session
from app.config.utils import mysql, MySQLdb


def data_article():
    daterange = session.get("daterange", "")
    multiselect = session.get("multiselect", [])

    if request.method == "POST" and request.is_json:
        data = request.get_json()
        id_article = data.get("id_article")
        sentiment = data.get("sentiment")

        if id_article and sentiment:
            try:
                cur = mysql.connection.cursor()
                update_query = """
                    UPDATE tb_article
                    SET sentiment = %s
                    WHERE id_article = %s
                """
                cur.execute(update_query, (sentiment, id_article))
                mysql.connection.commit()
                cur.close()

                return jsonify({"success": True})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)})

        return jsonify({"success": False, "error": "Invalid data"})

    return render_template(
        "article/article.html", daterange=daterange, multiselect=multiselect
    )
