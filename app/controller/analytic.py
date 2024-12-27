from flask import jsonify, render_template, request, session
from app.config.utils import mysql, MySQLdb


def data_analytic():

    return render_template("analytic/analytic.html")
