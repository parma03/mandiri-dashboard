from flask import flash, redirect, render_template, request, session, url_for
from app.config.utils import mysql, MySQLdb


def auth_index():
    if "logged_in" in session:
        return redirect(url_for("dashboard.index"))
    else:
        return redirect(url_for("auth.index"))


def auth_logout():
    if "id_user" in session:
        cur = mysql.connection.cursor()
        cur.execute(
            "UPDATE tb_user SET login_status = 0 WHERE id_user = %s",
            (session["id_user"],),
        )
        mysql.connection.commit()
        cur.close()

    session.clear()
    flash("Anda telah logout.", "success")
    return redirect(url_for("auth.index"))


def auth_login():
    title = "Login - Online Media Monitoring"
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        ip_address = request.remote_addr

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(
            "SELECT * FROM tb_user WHERE username=%s AND password=%s",
            (username, password),
        )
        data = cur.fetchone()

        if data:
            if data["login_status"] == 1:
                flash(
                    "Akun sedang digunakan. Tidak dapat login di beberapa perangkat.",
                    "danger",
                )
                return redirect(url_for("auth.index"))

            cur.execute(
                """
                UPDATE tb_user
                SET login_status = 1, ip_address = %s WHERE id_user = %s
            """,
                (ip_address, data["id_user"]),
            )
            mysql.connection.commit()

            session["logged_in"] = True
            session["id_user"] = data["id_user"]
            session["nama"] = data["nama"]
            session["email"] = data["email"]
            session["username"] = data["username"]
            session["role"] = data["role"]
            session["profile"] = data["profile"]
            session["ip_address"] = ip_address

            flash("Login berhasil!", "success")
            return redirect(url_for("dashboard.index"))

        flash("Username atau password salah!", "danger")
    return render_template("auth/index.html", title=title)
