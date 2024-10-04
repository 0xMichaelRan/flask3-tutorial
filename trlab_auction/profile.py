import flask
from flask import flash, render_template, session, g, request, redirect, url_for
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from werkzeug.utils import secure_filename
from werkzeug.exceptions import NotFound
import boto3
import os
import uuid
from botocore.exceptions import ClientError

from trlab_auction.database import get_db
from trlab_auction.auth import login_required
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Email

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


class ProfileForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=20)]
    )
    email = StringField("Email Address", validators=[DataRequired(), Email()])
    bio = TextAreaField("Bio", validators=[Length(max=500)])
    instagram_id = StringField("Instagram", validators=[Length(max=30)])
    youtube_id = StringField("Youtube", validators=[Length(max=30)])
    profile_photo = FileField(
        "Upload Avatar",
        validators=[
            FileAllowed(["jpg", "png", "jpeg", "gif"], "Images only!"),
            FileSize(
                max_size=5 * 1024 * 1024, message="File size must be less than 5MB."
            ),
        ],
    )
    cover_photo = FileField(
        "Upload Cover",
        validators=[
            FileAllowed(["jpg", "png", "jpeg", "gif"], "Images only!"),
            FileSize(
                max_size=10 * 1024 * 1024, message="File size must be less than 10MB."
            ),
        ],
    )


def upload_file_to_s3(file, bucket_name, folder):
    filename = secure_filename(file.filename)
    file_extension = os.path.splitext(filename)[1]
    user_id = flask.session.get("user_id")  # Get user_id from session
    unique_filename = f"{user_id}_{uuid.uuid4()}{file_extension}"
    s3_key = f"{folder}/{unique_filename}"

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
    form = ProfileForm()
    db = get_db()
    user_id = session.get("user_id")

    # Fetch user data
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
        user = cursor.fetchone()

    if user is None:
        raise NotFound("User not found.")

    if form.validate_on_submit():
        updates = {}
        for field in ["username", "email", "bio", "instagram_id", "youtube_id"]:
            if getattr(form, field).data != user[field]:
                updates[field] = getattr(form, field).data

        if updates:
            update_query = (
                "UPDATE user SET "
                + ", ".join(f"{key} = %s" for key in updates.keys())
                + " WHERE id = %s"
            )
            db = get_db()
            with db.cursor() as cursor:
                cursor.execute(update_query, (*updates.values(), user["id"]))
            db.commit()
            flash("Profile updated successfully!", "success")

        # Handle profile photo upload
        if form.profile_photo.data:
            try:
                file = form.profile_photo.data
                profile_photo_url = upload_file_to_s3(
                    file, BUCKET_NAME, PROFILE_PHOTO_FOLDER
                )
                if profile_photo_url:
                    db = get_db()
                    with db.cursor() as cursor:
                        cursor.execute(
                            "UPDATE user SET profile_photo_url = %s WHERE id = %s",
                            (profile_photo_url, user["id"]),
                        )
                    db.commit()
                    flash("Profile photo updated successfully!", "success")
                else:
                    flash("Failed to upload the photo. Please try again.", "error")
            except Exception as e:
                flash(f"An error occurred: {str(e)}", "error")

        # Handle cover photo upload
        if form.cover_photo.data:
            try:
                file = form.cover_photo.data
                cover_photo_url = upload_file_to_s3(
                    file, BUCKET_NAME, PROFILE_COVER_FOLDER
                )
                if cover_photo_url:
                    db = get_db()
                    with db.cursor() as cursor:
                        cursor.execute(
                            "UPDATE user SET cover_photo_url = %s WHERE id = %s",
                            (cover_photo_url, user["id"]),
                        )
                    db.commit()
                    flash("Cover photo updated successfully!", "success")
                else:
                    flash(
                        "Failed to upload the cover photo. Please try again.", "error"
                    )
            except Exception as e:
                flash(f"An error occurred: {str(e)}", "error")

        return redirect(url_for("profile.edit"))

    # Pre-fill the form with user data
    for field in ["username", "email", "bio", "instagram_id", "youtube_id"]:
        getattr(form, field).data = user[field]

    return render_template("profile/edit-profile.html", form=form, user=user)


# Account Settings Route
@bp.route("/settings", methods=("GET", "POST"))
def settings():
    return flask.render_template("profile/account-settings.html")


# Upload Artwork Route
@bp.route("/upload", methods=("GET", "POST"))
def upload():
    return flask.render_template("profile/upload-artwork.html")
