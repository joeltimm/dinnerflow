"""
Tonight page endpoint.

GET /api/tonight — return a selection of recipes to cook tonight
                   (sorted by least-recently-cooked, then fewest times cooked,
                    same algorithm as ironskillet/ui/pages/tonight.py)
"""
from fastapi import APIRouter, Depends

from database import get_db
from dependencies import get_current_user

router = APIRouter(prefix="/api/tonight", tags=["tonight"])


@router.get("")
def get_tonight_recipes(conn=Depends(get_db), user=Depends(get_current_user)):
    """
    Return up to 10 candidates for tonight's dinner:
    - Prioritise recipes that haven't been cooked recently
    - Sort by last_cooked ASC NULLS FIRST, then times_cooked ASC
    The frontend picks one at random (or lets the user re-roll).
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, title, source_url, local_image_path,
                   ingredients, instructions, rating, times_cooked, last_cooked, is_favorite
            FROM recipes
            WHERE user_id = %s
            ORDER BY last_cooked ASC NULLS FIRST, times_cooked ASC
            LIMIT 10
            """,
            (user["id"],),
        )
        return [dict(r) for r in cur.fetchall()]
