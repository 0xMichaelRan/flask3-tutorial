from trlab_auction.database import get_db

import flask
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from werkzeug.utils import secure_filename
import boto3
import os
from botocore.exceptions import ClientError
import uuid
from trlab_auction.auth import login_required
from flask import flash, render_template, session, g
from werkzeug.exceptions import NotFound

bp = flask.Blueprint("profile", __name__, url_prefix="/profile")


@bp.before_request
@login_required
def before_request():
    pass


# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
)

BUCKET_NAME = "theperfectbucket"
PROFILE_PHOTO_FOLDER = "profile_photos"
PROFILE_COVER_FOLDER = "profile_covers"


class ProfilePhotoForm(FlaskForm):
    photo = FileField(
        "Upload Avatar",
        validators=[
            FileAllowed(["jpg", "png", "jpeg", "gif"], "Images only!"),
            FileSize(
                max_size=5 * 1024 * 1024, message="File size must be less than 5MB."
            ),
        ],
    )


def upload_file_to_s3(file, bucket_name):
    # Remove debugging prints in production
    print(f"AWS Access Key ID: {os.environ.get('AWS_ACCESS_KEY_ID')}")
    print(f"AWS Secret Access Key: {os.environ.get('AWS_SECRET_ACCESS_KEY')}")

    filename = secure_filename(file.filename)
    file_extension = os.path.splitext(filename)[1]
    user_id = flask.session.get("user_id")  # Get user_id from session
    unique_filename = f"{user_id}_{uuid.uuid4()}{file_extension}"
    s3_key = f"{PROFILE_PHOTO_FOLDER}/{unique_filename}"

    try:
        s3_client.upload_fileobj(
            file,
            bucket_name,
            s3_key,
            ExtraArgs={"ContentType": file.content_type},
        )
        print(f"File uploaded successfully: {s3_key}")
    except ClientError as e:
        print(f"Error uploading file: {e}")
        return None

    return f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"


@bp.route("/edit", methods=("GET", "POST"))
def edit():
    form = ProfilePhotoForm()
    if form.validate_on_submit():
        if form.photo.data:
            try:
                file_url = upload_file_to_s3(form.photo.data, BUCKET_NAME)
                if file_url:
                    db = get_db()
                    user_id = session.get('user_id')
                    user = db.execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()
                    if user:
                        db.execute(
                            'UPDATE user SET profile_photo_url = ? WHERE id = ?',
                            (file_url, user_id)
                        )
                        db.commit()
                        flash("Profile photo updated successfully!", "success")
                    else:
                        raise NotFound("User not found.")
                else:
                    flash("Failed to upload the photo. Please try again.", "error")
            except Exception as e:
                flash(f"An error occurred: {str(e)}", "error")
        else:
            flash("No photo was selected for upload.", "warning")
    elif form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", "error")

    return render_template("profile/edit-profile.html", form=form)


@bp.route("/settings", methods=("GET", "POST"))
def settings():
    return flask.render_template("profile/account-settings.html")


@bp.route("/upload", methods=("GET", "POST"))
def upload():
    return flask.render_template("profile/upload-artwork.html")
