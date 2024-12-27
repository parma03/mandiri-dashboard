import os
from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from app.config.utils import mysql, MySQLdb
import uuid


def admin_index():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == "POST" and "tambah" in request.form:
        nama = request.form["nama"]
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        role = "Administrator"

        cur.execute(
            "SELECT * FROM tb_user WHERE username = %s OR email = %s",
            (username, email),
        )
        existing_user = cur.fetchone()

        if existing_user:
            flash(
                "Username atau email sudah terdaftar, silakan gunakan yang lain.",
                "danger",
            )
            return redirect(url_for("user.admin"))
        else:
            cur.execute(
                """INSERT INTO tb_user(nama, username, password, email, role) 
                VALUES (%s, %s, %s, %s, %s)""",
                (nama, username, password, email, role),
            )
            mysql.connection.commit()
            flash("Akun berhasil dibuat!", "success")
            return redirect(url_for("user.admin"))

    if request.method == "POST" and "edit" in request.form:
        id = request.form.get("id", None)
        nama = request.form["nama"]
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        profile = request.files.get("profile")

        # Ambil data pengguna lama
        cur.execute("SELECT * FROM tb_user WHERE id_user = %s", (id,))
        user = cur.fetchone()

        if not user:
            flash("Pengguna tidak ditemukan.", "danger")
            return redirect(url_for("user.admin"))

        # Cek perubahan username/email
        if username != user["username"] or email != user["email"]:
            cur.execute(
                """
                SELECT * FROM tb_user 
                WHERE (username = %s OR email = %s) AND id_user != %s
                """,
                (username, email, id),
            )
            existing_user = cur.fetchone()

            if existing_user:
                flash(
                    "Username atau email sudah terdaftar, silakan gunakan yang lain.",
                    "danger",
                )
                return redirect(url_for("user.admin"))

        # Update profil jika file baru diunggah
        if profile:
            file_ext = os.path.splitext(profile.filename)[1]
            random_filename = f"{uuid.uuid4()}{file_ext}"
            if user["profile"]:
                old_file_path = os.path.join(
                    current_app.root_path, "app/static/profile/", user["profile"]
                )
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

            filename = random_filename
            profile_path = os.path.join(
                current_app.root_path, "app/static/profile/", filename
            )
            profile.save(profile_path)
        else:
            filename = user["profile"]

        # Update data ke database
        cur.execute(
            """
            UPDATE tb_user 
            SET 
                nama = %s,
                username = %s,
                password = %s,
                email = %s,
                profile = %s
            WHERE
                id_user = %s
            """,
            (nama, username, password, email, filename, id),
        )
        mysql.connection.commit()
        flash("Akun berhasil diupdate!", "success")
        return redirect(url_for("user.admin"))

    if request.method == "POST" and "delete" in request.form:
        id = request.form.get("id", None)

        # Ambil data pengguna lama
        cur.execute("SELECT * FROM tb_user WHERE id_user = %s", (id,))
        user = cur.fetchone()

        if not user:
            flash("Pengguna tidak ditemukan.", "danger")
            return redirect(url_for("user.admin"))

        # Hapus file profile jika ada
        if user["profile"]:
            profile_path = os.path.join(
                current_app.root_path, "app/static/profile/", user["profile"]
            )
            if os.path.exists(profile_path):
                try:
                    os.remove(profile_path)
                except OSError as e:
                    flash(f"Error menghapus file profile: {str(e)}", "warning")

        cur.execute("DELETE FROM tb_user WHERE id_user = %s", (id,))
        mysql.connection.commit()

        cur.execute(
            """
            DELETE FROM tb_user 
            WHERE
                id_user = %s
            """,
            (id),
        )
        mysql.connection.commit()
        flash("Akun berhasil dihapus!", "success")
        return redirect(url_for("user.admin"))

    cur.execute(""" SELECT * FROM tb_user WHERE role = 'Administrator' """)
    admin = cur.fetchall()
    cur.close()
    return render_template("user/admin.html", admins=admin)


def operator_index():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == "POST" and "tambah" in request.form:
        nama = request.form["nama"]
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        role = "Operator"

        cur.execute(
            "SELECT * FROM tb_user WHERE username = %s OR email = %s",
            (username, email),
        )
        existing_user = cur.fetchone()

        if existing_user:
            flash(
                "Username atau email sudah terdaftar, silakan gunakan yang lain.",
                "danger",
            )
            return redirect(url_for("user.operator"))
        else:
            cur.execute(
                """INSERT INTO tb_user(nama, username, password, email, role) 
                VALUES (%s, %s, %s, %s, %s)""",
                (nama, username, password, email, role),
            )
            mysql.connection.commit()
            flash("Akun berhasil dibuat!", "success")
            return redirect(url_for("user.operator"))

    if request.method == "POST" and "edit" in request.form:
        id = request.form.get("id", None)
        nama = request.form["nama"]
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        profile = request.files.get("profile")

        # Ambil data pengguna lama
        cur.execute("SELECT * FROM tb_user WHERE id_user = %s", (id,))
        user = cur.fetchone()

        if not user:
            flash("Pengguna tidak ditemukan.", "danger")
            return redirect(url_for("user.operator"))

        # Cek perubahan username/email
        if username != user["username"] or email != user["email"]:
            cur.execute(
                """
                SELECT * FROM tb_user 
                WHERE (username = %s OR email = %s) AND id_user != %s
                """,
                (username, email, id),
            )
            existing_user = cur.fetchone()

            if existing_user:
                flash(
                    "Username atau email sudah terdaftar, silakan gunakan yang lain.",
                    "danger",
                )
                return redirect(url_for("user.operator"))

        # Update profil jika file baru diunggah
        if profile:
            file_ext = os.path.splitext(profile.filename)[1]
            random_filename = f"{uuid.uuid4()}{file_ext}"
            if user["profile"]:
                old_file_path = os.path.join(
                    current_app.root_path, "app/static/profile/", user["profile"]
                )
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

            filename = random_filename
            profile_path = os.path.join(
                current_app.root_path, "app/static/profile/", filename
            )
            profile.save(profile_path)
        else:
            filename = user["profile"]

        # Update data ke database
        cur.execute(
            """
            UPDATE tb_user 
            SET 
                nama = %s,
                username = %s,
                password = %s,
                email = %s,
                profile = %s
            WHERE
                id_user = %s
            """,
            (nama, username, password, email, filename, id),
        )
        mysql.connection.commit()
        flash("Akun berhasil diupdate!", "success")
        return redirect(url_for("user.operator"))

    if request.method == "POST" and "delete" in request.form:
        id = request.form.get("id", None)

        # Ambil data pengguna lama
        cur.execute("SELECT * FROM tb_user WHERE id_user = %s", (id,))
        user = cur.fetchone()

        if not user:
            flash("Pengguna tidak ditemukan.", "danger")
            return redirect(url_for("user.operator"))

        # Hapus file profile jika ada
        if user["profile"]:
            profile_path = os.path.join(
                current_app.root_path, "app/static/profile/", user["profile"]
            )
            if os.path.exists(profile_path):
                try:
                    os.remove(profile_path)
                except OSError as e:
                    flash(f"Error menghapus file profile: {str(e)}", "warning")

        cur.execute("DELETE FROM tb_user WHERE id_user = %s", (id,))
        mysql.connection.commit()

        cur.execute(
            """
            DELETE FROM tb_user 
            WHERE
                id_user = %s
            """,
            (id),
        )
        mysql.connection.commit()
        flash("Akun berhasil dihapus!", "success")
        return redirect(url_for("user.operator"))

    cur.execute(""" SELECT * FROM tb_user WHERE role = 'Operator' """)
    operator = cur.fetchall()
    cur.close()

    return render_template("user/operator.html", operators=operator)


def viewer_index():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == "POST" and "tambah" in request.form:
        nama = request.form["nama"]
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        role = "Viewer"

        cur.execute(
            "SELECT * FROM tb_user WHERE username = %s OR email = %s",
            (username, email),
        )
        existing_user = cur.fetchone()

        if existing_user:
            flash(
                "Username atau email sudah terdaftar, silakan gunakan yang lain.",
                "danger",
            )
            return redirect(url_for("user.viewer"))
        else:
            cur.execute(
                """INSERT INTO tb_user(nama, username, password, email, role) 
                VALUES (%s, %s, %s, %s, %s)""",
                (nama, username, password, email, role),
            )
            mysql.connection.commit()
            flash("Akun berhasil dibuat!", "success")
            return redirect(url_for("user.viewer"))

    if request.method == "POST" and "edit" in request.form:
        id = request.form.get("id", None)
        nama = request.form["nama"]
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        profile = request.files.get("profile")

        # Ambil data pengguna lama
        cur.execute("SELECT * FROM tb_user WHERE id_user = %s", (id,))
        user = cur.fetchone()

        if not user:
            flash("Pengguna tidak ditemukan.", "danger")
            return redirect(url_for("user.viewer"))

        # Cek perubahan username/email
        if username != user["username"] or email != user["email"]:
            cur.execute(
                """
                SELECT * FROM tb_user 
                WHERE (username = %s OR email = %s) AND id_user != %s
                """,
                (username, email, id),
            )
            existing_user = cur.fetchone()

            if existing_user:
                flash(
                    "Username atau email sudah terdaftar, silakan gunakan yang lain.",
                    "danger",
                )
                return redirect(url_for("user.viewer"))

        # Update profil jika file baru diunggah
        if profile:
            file_ext = os.path.splitext(profile.filename)[1]
            random_filename = f"{uuid.uuid4()}{file_ext}"
            if user["profile"]:
                old_file_path = os.path.join(
                    current_app.root_path, "app/static/profile/", user["profile"]
                )
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

            filename = random_filename
            profile_path = os.path.join(
                current_app.root_path, "app/static/profile/", filename
            )
            profile.save(profile_path)
        else:
            filename = user["profile"]

        # Update data ke database
        cur.execute(
            """
            UPDATE tb_user 
            SET 
                nama = %s,
                username = %s,
                password = %s,
                email = %s,
                profile = %s
            WHERE
                id_user = %s
            """,
            (nama, username, password, email, filename, id),
        )
        mysql.connection.commit()
        flash("Akun berhasil diupdate!", "success")
        return redirect(url_for("user.viewer"))

    if request.method == "POST" and "delete" in request.form:
        id = request.form.get("id", None)

        # Ambil data pengguna lama
        cur.execute("SELECT * FROM tb_user WHERE id_user = %s", (id,))
        user = cur.fetchone()

        if not user:
            flash("Pengguna tidak ditemukan.", "danger")
            return redirect(url_for("user.viewer"))

        # Hapus file profile jika ada
        if user["profile"]:
            profile_path = os.path.join(
                current_app.root_path, "app/static/profile/", user["profile"]
            )
            if os.path.exists(profile_path):
                try:
                    os.remove(profile_path)
                except OSError as e:
                    flash(f"Error menghapus file profile: {str(e)}", "warning")

        cur.execute("DELETE FROM tb_user WHERE id_user = %s", (id,))
        mysql.connection.commit()

        cur.execute(
            """
            DELETE FROM tb_user 
            WHERE
                id_user = %s
            """,
            (id),
        )
        mysql.connection.commit()
        flash("Akun berhasil dihapus!", "success")
        return redirect(url_for("user.operator"))

    cur.execute(""" SELECT * FROM tb_user WHERE role = 'Viewer' """)
    viewer = cur.fetchall()
    cur.close()

    return render_template("user/viewer.html", viewers=viewer)
