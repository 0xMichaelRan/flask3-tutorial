import flask
from flask import flash, render_template, session, g, request, redirect, url_for
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from werkzeug.utils import secure_filename
from werkzeug.exceptions import NotFound
from werkzeug.security import generate_password_hash
import boto3
import os
import uuid
import re
from botocore.exceptions import ClientError
from flask import current_app
from datetime import datetime
import json

from trlab_auction.database import get_db
from trlab_auction.auth import login_required
from wtforms import StringField, TextAreaField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo

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


class SettingsForm(FlaskForm):
    new_password = PasswordField("New Password", validators=[Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[EqualTo("new_password")]
    )
    bid_activity = BooleanField("Bid Activity")
    item_sold = BooleanField("Item Sold")
    added_to_collection = BooleanField("Added to a collection")
    review = BooleanField("Review")


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
@login_required
def edit():
    form = ProfileForm()
    user = g.user
    db = get_db()

    if request.method == "POST":
        if form.validate_on_submit():
            updates = {}
            has_error = False
            history_updates = []
            current_time = datetime.utcnow()

            fields_to_update = [
                ("username", 3, 20),
                ("email", None, None),
                ("bio", None, 500),
                ("instagram_id", None, 30),
                ("youtube_id", None, 30)
            ]

            for field, min_length, max_length in fields_to_update:
                new_value = getattr(form, field).data.strip()
                if field in ['instagram_id', 'youtube_id']:
                    new_value = new_value.lstrip('@')

                if new_value != user[field]:
                    if min_length and len(new_value) < min_length:
                        flash(f"{field.capitalize()} must be at least {min_length} characters long.", "dark")
                        has_error = True
                    elif max_length and len(new_value) > max_length:
                        flash(f"{field.capitalize()} must be {max_length} characters or less.", "dark")
                        has_error = True
                    elif field == "username" and not new_value.isalnum():
                        flash("Username must contain only letters and numbers.", "dark")
                        has_error = True
                    elif field == "email" and "@" not in new_value:
                        flash("Invalid email address.", "dark")
                        has_error = True
                    else:
                        updates[field] = new_value
                        history_updates.append((
                            current_time,
                            user["id"],
                            field,
                            json.dumps(user[field]),
                            json.dumps(new_value)
                        ))

            # Handle photo uploads
            for photo_field in ['profile_photo', 'cover_photo']:
                if getattr(form, photo_field).data:
                    try:
                        file = getattr(form, photo_field).data
                        folder = PROFILE_PHOTO_FOLDER if photo_field == 'profile_photo' else PROFILE_COVER_FOLDER
                        photo_url = upload_file_to_s3(file, BUCKET_NAME, folder)
                        if photo_url:
                            updates[f"{photo_field}_url"] = photo_url
                            history_updates.append((
                                current_time,
                                user["id"],
                                f"{photo_field}_url",
                                json.dumps(user.get(f"{photo_field}_url")),
                                json.dumps(photo_url)
                            ))
                        else:
                            flash(f"Failed to upload the {photo_field.replace('_', ' ')}. Please try again.", "error")
                            has_error = True
                    except Exception as e:
                        flash(f"An error occurred while uploading {photo_field.replace('_', ' ')}: {str(e)}", "error")
                        has_error = True

            if not has_error and updates:
                try:
                    with db.cursor() as cursor:
                        # Update user table
                        update_query = (
                            "UPDATE user SET "
                            + ", ".join(f"{key} = %s" for key in updates.keys())
                            + " WHERE id = %s"
                        )
                        cursor.execute(update_query, (*updates.values(), user["id"]))

                        # Insert into profile_update_history
                        history_insert_query = """
                        INSERT INTO profile_update_history 
                        (timestamp, user_id, field_name, old_value, new_value)
                        VALUES (%s, %s, %s, %s, %s)
                        """
                        cursor.executemany(history_insert_query, history_updates)

                    db.commit()
                    flash("Profile updated successfully!", "success")

                    # Refresh user data after update
                    with db.cursor() as cursor:
                        cursor.execute("SELECT * FROM user WHERE id = %s", (user["id"],))
                        g.user = cursor.fetchone()
                    user = g.user
                except Exception as e:
                    db.rollback()
                    current_app.logger.error(f"Database error: {str(e)}")
                    flash("An error occurred while updating your profile. Please try again.", "error")
            elif not updates:
                flash("No changes were made to your profile.", "info")

        return redirect(url_for('profile.edit'))

    # GET request: Pre-fill the form with user data
    for field in ["username", "email", "bio", "instagram_id", "youtube_id"]:
        getattr(form, field).data = user[field]

    return render_template("profile/edit.html", form=form, user=user)


# Account Settings Route
@bp.route("/settings", methods=("GET", "POST"))
@login_required
def settings():
    form = SettingsForm()
    db = get_db()
    user_id = session.get("user_id")

    if request.method == "POST":
        # Handle form submission
        updates = {}

        # Handle password change
        if (
            form.new_password.data
            and form.new_password.data == form.confirm_password.data
        ):
            updates["password"] = generate_password_hash(form.new_password.data)

        # Handle checkbox fields
        checkbox_fields = ["bid_activity", "item_sold", "added_to_collection", "review"]
        for field in checkbox_fields:
            updates[f"notification_{field}"] = field in request.form

        # Update database if there are changes
        if updates:
            update_query = (
                "UPDATE user SET "
                + ", ".join(f"{key} = %s" for key in updates.keys())
                + " WHERE id = %s"
            )
            with db.cursor() as cursor:
                cursor.execute(update_query, (*updates.values(), user_id))
            db.commit()
            flash("Settings updated successfully!", "success")
        else:
            flash("No changes were made.", "info")

        return redirect(url_for("profile.settings"))

    # GET request: Pre-fill the form with user data
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
        user = cursor.fetchone()

    if user:
        form.bid_activity.data = bool(user.get("notification_bid_activity"))
        form.item_sold.data = bool(user.get("notification_item_sold"))
        form.added_to_collection.data = bool(
            user.get("notification_added_to_collection")
        )
        form.review.data = bool(user.get("notification_review"))

    return render_template("profile/settings.html", form=form)


# Upload Artwork Route
@bp.route("/upload", methods=("GET", "POST"))
def upload():
    return flask.render_template("profile/upload.html")