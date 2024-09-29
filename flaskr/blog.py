from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

# unlike bp = Blueprint('auth', __name__, url_prefix='/auth')
# the blog blueprint does not have a url_prefix. 
#  So the index view will be at /, the create view at /create, and so on.
bp = Blueprint('blog', __name__)
