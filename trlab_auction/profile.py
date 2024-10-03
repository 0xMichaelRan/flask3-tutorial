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
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    bio = TextAreaField('Bio', validators=[Length(max=500)])
    instagram_id = StringField('Instagram', validators=[Length(max=30)])
    youtube_id = StringField('Youtube', validators=[Length(max=30)])
    profile_photo = FileField(
        "Upload Avatar",
        validators=[
            FileAllowed(["jpg", "png", "jpeg", "gif"], "Images only!"),
            FileSize(max_size=5 * 1024 * 1024, message="File size must be less than 5MB.")
        ]
    )
    cover_photo = FileField(
        "Upload Cover",
        validators=[
            FileAllowed(["jpg", "png", "jpeg", "gif"], "Images only!"),
            FileSize(max_size=10 * 1024 * 1024, message="File size must be less than 10MB.")
        ]
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
    user_id = session.get('user_id')
    user = db.execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        raise NotFound("User not found.")
    
    if request.method == 'GET':
        form.username.data = user['username']
        form.email.data = user['email']
        form.bio.data = user['bio'] if 'bio' in user.keys() else ''
        form.instagram_id.data = user['instagram_id'] if 'instagram_id' in user.keys() else ''
        form.youtube_id.data = user['youtube_id'] if 'youtube_id' in user.keys() else ''
    
    if form.validate_on_submit():
        updates = {
            'username': form.username.data,
            'email': form.email.data,
            'bio': form.bio.data,
            'instagram_id': form.instagram_id.data,
            'youtube_id': form.youtube_id.data
        }
        
        if form.profile_photo.data:
            try:
                file_url = upload_file_to_s3(form.profile_photo.data, BUCKET_NAME, PROFILE_PHOTO_FOLDER)
                if file_url:
                    updates['profile_photo_url'] = file_url
                else:
                    flash("Failed to upload the profile photo. Please try again.", "error")
            except Exception as e:
                flash(f"An error occurred while uploading profile photo: {str(e)}", "error")
        
        if form.cover_photo.data:
            try:
                file_url = upload_file_to_s3(form.cover_photo.data, BUCKET_NAME, PROFILE_COVER_FOLDER)
                if file_url:
                    updates['cover_photo_url'] = file_url
                else:
                    flash("Failed to upload the cover photo. Please try again.", "error")
            except Exception as e:
                flash(f"An error occurred while uploading cover photo: {str(e)}", "error")
        
        update_query = 'UPDATE user SET ' + ', '.join(f'{key} = ?' for key in updates.keys()) + ' WHERE id = ?'
        db.execute(update_query, (*updates.values(), user_id))
        db.commit()
        flash("Profile updated successfully! It may take a while for changes to show up.", "success")
        return redirect(url_for('profile.edit'))  # Redirect after successful update
    
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", "error")

    return render_template("profile/edit-profile.html", form=form)


# Account Settings Route
@bp.route("/settings", methods=("GET", "POST"))
def settings():
    return flask.render_template("profile/account-settings.html")


# Upload Artwork Route
@bp.route("/upload", methods=("GET", "POST"))
def upload():
    return flask.render_template("profile/upload-artwork.html")
