import os
from flask import Flask, render_template
from dotenv import load_dotenv

from . import database
from .src.auth import bp as auth_bp
from .src.profile import bp as profile_bp
from .src.art.artwork import bp as art_bp

# Load environment variables
load_dotenv()


# The application factory function
def create_app(test_config=None):
    # create and configure the app

    # The app is in a package (trlab_auction) and you import it, __name__ being "trlab_auction"
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="trlab_auction_dev",
        DATABASE=os.path.join(app.instance_path, "trlab_auction.sqlite"),
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(art_bp)

    database.init_app(app)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route("/")
    def hello():
        return "This is the landing page of trlab_auction."

    @app.route("/item")
    def item():
        return render_template("item.html")

    @app.route("/home")
    def home():
        return render_template("home.html")

    return app
