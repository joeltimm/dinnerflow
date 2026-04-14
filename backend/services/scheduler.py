"""
Meal plan logic.

The scheduling itself is handled by Celery Beat (see celery_app.py).
This module contains the per-user meal plan builder that Celery tasks call.

send_meal_plan_for_user(user_id, email, name) is also called directly by
the /api/chef/email-plan endpoint for on-demand triggers.
"""
import logging

import psycopg2.extras
from services.search import search_recipes

from auth.tokens import make_email_token, make_unsubscribe_token
from config import get_settings
from database import get_connection
from services import llm as llm_svc
from services.email import send_meal_plan_email

logger = logging.getLogger(__name__)


# ── Core meal plan logic ──────────────────────────────────────────────────────

def send_meal_plan_for_user(user_id: int, email: str, name: str) -> None:
    """
    Build and send a weekly meal plan email for a single user.

    Flow (replicates n8n 'Ironskillet' workflow):
    1. Load user preferences + favorite recipe titles from DB
    2. Use Tavily to search for new recipe ideas
    3. Mix in 1-2 favorites as suggestions
    4. Format + send HTML email with signed action links
    """
    settings = get_settings()

    with get_connection() as conn:
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        with conn.cursor() as cur:
            cur.execute(
                "SELECT dietary_preferences FROM users WHERE id = %s", (user_id,)
            )
            row = cur.fetchone()
            prefs = (row["dietary_preferences"] or "") if row else ""

            cur.execute(
                "SELECT title, source_url FROM recipes "
                "WHERE user_id = %s AND is_favorite = true ORDER BY rating DESC LIMIT 5",
                (user_id,),
            )
            favorites = [dict(r) for r in cur.fetchall()]

    recipes: list[dict] = []

    # Add 1 favorite as a reminder
    if favorites:
        fav = favorites[0]
        recipes.append({
            "title": fav["title"],
            "url": fav.get("source_url") or "",
            "description": "A tried-and-true favourite from your recipe vault.",
            "is_favorite": True,
        })

    # Find new recipe ideas via web search.
    # search_recipes() tries Tavily first, falls back to DuckDuckGo automatically
    # on any failure (no key, quota exceeded, 429, network error, etc.).
    # If both fail, we fall back further to LLM-only ideas without URLs.
    fav_names = [f["title"] for f in favorites]
    prefs_clause = f" that are {prefs}" if prefs else ""
    fav_clause = f" (user likes: {', '.join(fav_names[:3])})" if fav_names else ""

    queries = [
        f"easy healthy dinner recipe{prefs_clause}",
        f"quick weeknight meal idea{prefs_clause}{fav_clause}",
        f"30-minute dinner recipe{prefs_clause}",
    ]

    seen_urls: set[str] = set()
    search_succeeded = False

    for query in queries:
        if len(recipes) >= 5:
            break
        results = search_recipes(query, max_results=2)
        if results:
            search_succeeded = True
        for r in results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                recipes.append({
                    "title": r["title"] or "New Recipe Idea",
                    "url": url,
                    "description": r["description"],
                    "is_favorite": False,
                })

    if not search_succeeded:
        # Both Tavily and DuckDuckGo failed — ask the LLM to suggest ideas.
        # These won't have URLs, but the email still delivers value.
        logger.warning("All web search backends failed — using LLM-only fallback for meal plan")
        try:
            ideas = llm_svc.generate_meal_ideas(prefs, fav_names, n=4)
            for idea in ideas:
                recipes.append({
                    "title": idea["title"],
                    "url": "",
                    "description": idea.get("description", ""),
                    "is_favorite": False,
                })
        except Exception as exc:
            logger.error("LLM fallback for meal plan also failed: %s", exc)

    if not recipes:
        logger.warning("No recipes to send for user %d — skipping email", user_id)
        return

    # Signed token for 'Add to My Recipes' email links (valid 7 days)
    select_token = make_email_token(user_id)
    unsub_token = make_unsubscribe_token(user_id)

    send_meal_plan_email(
        to_email=email,
        user_name=name or "Chef",
        user_id=user_id,
        recipes=recipes,
        select_token=select_token,
        unsub_token=unsub_token,
    )
    logger.info("Meal plan email sent to %s (%d recipes)", email, len(recipes))
