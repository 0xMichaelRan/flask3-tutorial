import flask
from flask import render_template, request, redirect, url_for, flash


bp = flask.Blueprint("art", __name__, url_prefix="/art")


@bp.route("/item/<int:id>")
def item(id):
    return render_template("art/item.html", id=id)
