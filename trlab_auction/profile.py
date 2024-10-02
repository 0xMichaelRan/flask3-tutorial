import flask
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from werkzeug.utils import secure_filename
import boto3
import os
from botocore.exceptions import ClientError
import uuid

bp = flask.Blueprint("profile", __name__, url_prefix="/profile")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
)

BUCKET_NAME = "theperfectbucket"


class ProfilePhotoForm(FlaskForm):
    photo = FileField(
        "Upload Avatar",
        validators=[
            FileAllowed(["jpg", "png", "jpeg", "gif"], "Images only!"),
            FileSize(max_size=500 * 1024, message="File size must be less than 500KB."),
        ],
    )

def upload_file_to_s3(file, bucket_name, user_id):
    # Remove debugging prints in production
    print(f"AWS Access Key ID: {os.environ.get('AWS_ACCESS_KEY_ID')}")
    print(f"AWS Secret Access Key: {os.environ.get('AWS_SECRET_ACCESS_KEY')}")

    filename = secure_filename(file.filename)
    file_extension = os.path.splitext(filename)[1]
    unique_filename = f"{user_id}_{uuid.uuid4()}{file_extension}"
    s3_key = f"profile_photo/{unique_filename}"

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
            file_url = upload_file_to_s3(form.photo.data, BUCKET_NAME, "USER_ID")
            if file_url:
                # Update user's profile photo URL in the database
                # This is a placeholder - replace with your actual database update logic
                # current_user.profile_photo_url = file_url
                # db.session.commit()
                flask.flash("Profile photo updated successfully!", "success")
            else:
                flask.flash("Error uploading profile photo.", "error")
    return flask.render_template("profile/edit-profile.html", form=form)


@bp.route("/settings", methods=("GET", "POST"))
def settings():
    return flask.render_template("profile/account-settings.html")


@bp.route("/upload", methods=("GET", "POST"))
def upload():
    return flask.render_template("profile/upload-artwork.html")
