from flask import render_template, session


def dashboard_index():
    daterange = session.get("daterange", "")
    multiselect = session.get("multiselect", [])

    return render_template(
        "dashboard/index.html", daterange=daterange, multiselect=multiselect
    )
