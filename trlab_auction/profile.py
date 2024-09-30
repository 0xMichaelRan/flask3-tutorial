import flask

bp = flask.Blueprint("profile", __name__, url_prefix="/profile")


@bp.route("/edit", methods=("GET", "POST"))
def edit():
    return flask.render_template("profile/edit-profile.html")


@bp.route("/settings", methods=("GET", "POST"))
def settings():
    return flask.render_template("profile/account-settings.html")


@bp.route("/upload", methods=("GET", "POST"))
def upload():
    return flask.render_template("profile/upload-artwork.html")
