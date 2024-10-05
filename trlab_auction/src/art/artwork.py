from flask import Blueprint, render_template, abort
from trlab_auction.database import get_db
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bp = Blueprint("art", __name__, url_prefix="/art")


@bp.route("/item/<int:id>")
def item(id):
    db = get_db()
    cursor = None
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT a.*, u.username as artist_name 
            FROM artwork a 
            JOIN user u ON a.user_id = u.id  
            WHERE a.id = %s
        """,
            (id,),
        )
        result = cursor.fetchone()

        if result is None:
            logger.warning(f"Artwork with id {id} not found")
            abort(404)  # Artwork not found
        else:
            logger.info(f"Artwork found: {result}")

        # Convert result to dictionary
        columns = [col[0] for col in cursor.description]
        artwork = dict(zip(columns, result))

        logger.info(f"Fetched artwork: {artwork}")

        return render_template("art/item.html", artwork=result)
    except Exception as e:
        logger.error(f"Error fetching artwork: {e}", exc_info=True)
        abort(500)  # Internal server error
    finally:
        if cursor:
            cursor.close()
