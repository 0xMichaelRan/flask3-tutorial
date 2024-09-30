import flask

bp = flask.Blueprint("profile", __name__, url_prefix="/profile")


@bp.route("/edit", methods=("GET", "POST"))
def profile():
    return flask.render_template("profile/edit-profile.html")


@bp.route("/settings", methods=("GET", "POST"))
def account_settings():
    return flask.render_template("profile/account-settings.html")


@bp.route("/upload", methods=("GET", "POST"))
def upload():
    return flask.render_template("profile/upload-artwork.html")
