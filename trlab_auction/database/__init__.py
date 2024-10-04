import os
import pymysql
import click
from flask import current_app, g
from flask.cli import with_appcontext
from dotenv import load_dotenv

load_dotenv()


def get_db():
    if "db" not in g:
        g.db = pymysql.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
            cursorclass=pymysql.cursors.DictCursor,
        )
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    # Create database if it doesn't exist
    conn = pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {os.getenv('MYSQL_DATABASE')}"
            )
        conn.commit()
    finally:
        conn.close()

    # Now connect to the database and create tables
    db = get_db()
    try:
        with current_app.open_resource("database/schema.sql") as f:
            sql_script = f.read().decode("utf8")
            statements = sql_script.split(";")
            with db.cursor() as cursor:
                for statement in statements:
                    if statement.strip():
                        try:
                            cursor.execute(statement)
                        except pymysql.err.OperationalError as e:
                            if e.args[0] != 1051:  # Ignore "Unknown table" warnings
                                current_app.logger.warning(f"Error executing SQL: {e}")
                                raise
        db.commit()
    except Exception as e:
        current_app.logger.error(f"Database initialization error: {e}")
        raise


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
