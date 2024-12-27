from flask import jsonify, render_template, request, session
from app.config.utils import mysql, MySQLdb


def group_index():

    return render_template("group/group.html")
