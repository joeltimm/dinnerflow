"""
Dashboard analytics endpoint + onboarding status.

GET /api/dashboard    — returns stats and chart data for the current user
GET /api/onboarding   — lightweight checklist flags for first-run UX
"""
from fastapi import APIRouter, Depends

from database import get_db
from dependencies import get_current_user

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/onboarding")
def get_onboarding(conn=Depends(get_db), user=Depends(get_current_user)):
    """Lightweight checklist flags for the first-run onboarding UX."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS recipe_count, "
            "       COALESCE(SUM(times_cooked), 0) AS total_cooked "
            "FROM recipes WHERE user_id = %s",
            (user["id"],),
        )
        stats = dict(cur.fetchone())

    return {
        "has_recipes": stats["recipe_count"] > 0,
        "has_dietary_prefs": bool(user.get("dietary_preferences")),
        "has_cooked": int(stats["total_cooked"]) > 0,
        "recipe_count": int(stats["recipe_count"]),
    }


@router.get("/dashboard")
def get_dashboard(conn=Depends(get_db), user=Depends(get_current_user)):
    uid = user["id"]

    with conn.cursor() as cur:
        # Top-level counts
        cur.execute(
            "SELECT COUNT(*) AS total_recipes, "
            "       COALESCE(SUM(times_cooked), 0) AS total_cooked, "
            "       COUNT(*) FILTER (WHERE is_favorite) AS total_favorites "
            "FROM recipes WHERE user_id = %s",
            (uid,),
        )
        totals = dict(cur.fetchone())

        # Top 10 most-cooked recipes
        cur.execute(
            """
            SELECT title, times_cooked
            FROM recipes
            WHERE user_id = %s AND times_cooked > 0
            ORDER BY times_cooked DESC
            LIMIT 10
            """,
            (uid,),
        )
        most_cooked = [dict(r) for r in cur.fetchall()]

        # Top 10 highest-rated recipes
        cur.execute(
            """
            SELECT title, rating
            FROM recipes
            WHERE user_id = %s AND rating > 0
            ORDER BY rating DESC
            LIMIT 10
            """,
            (uid,),
        )
        highest_rated = [dict(r) for r in cur.fetchall()]

        # Recent cooking log (last 10 entries)
        cur.execute(
            """
            SELECT r.title, cl.date_cooked, cl.rating, cl.notes
            FROM cooking_log cl
            JOIN recipes r ON r.id = cl.recipe_id
            WHERE r.user_id = %s
            ORDER BY cl.date_cooked DESC
            LIMIT 10
            """,
            (uid,),
        )
        recent_log = [dict(r) for r in cur.fetchall()]

    return {
        **totals,
        "most_cooked": most_cooked,
        "highest_rated": highest_rated,
        "recent_log": recent_log,
    }
