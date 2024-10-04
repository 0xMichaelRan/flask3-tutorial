import os
import sqlite3
import pymysql
import click
from flask import current_app, g
from flask.cli import with_appcontext
from dotenv import load_dotenv

load_dotenv()


def get_db():
    if "db" not in g:
        db_type = os.getenv("DB_TYPE", "sqlite").lower()

        if db_type == "sqlite":
            g.db = sqlite3.connect(
                current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = sqlite3.Row
        elif db_type == "mysql":
            g.db = pymysql.connect(
                host=os.getenv("MYSQL_HOST"),
                user=os.getenv("MYSQL_USER"),
                password=os.getenv("MYSQL_PASSWORD"),
                database=os.getenv("MYSQL_DATABASE"),
                cursorclass=pymysql.cursors.DictCursor,
            )
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    return g.db


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        if isinstance(db, sqlite3.Connection):
            db.close()
        elif isinstance(db, pymysql.Connection):
            db.close()


def init_db():
    db = get_db()
    db_type = os.getenv("DB_TYPE", "sqlite").lower()

    if db_type == "sqlite":
        with current_app.open_resource("database/setup-db.sql") as f:
            db.executescript(f.read().decode("utf8"))
    elif db_type == "mysql":
        with current_app.open_resource("schema_mysql.sql") as f:
            with db.cursor() as cursor:
                cursor.execute(f.read().decode("utf8"))
        db.commit()


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
