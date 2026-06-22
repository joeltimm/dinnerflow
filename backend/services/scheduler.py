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
    fav_names = [f["title"] for f in favorites]
    target = 5
    seen_urls: set[str] = set()

    # Add 1 favorite as a reminder
    if favorites:
        fav = favorites[0]
        recipes.append({
            "title": fav["title"],
            "url": fav.get("source_url") or "",
            "description": "A tried-and-true favourite from your recipe vault.",
            "is_favorite": True,
        })

    # LLM-first idea generation: the model returns clean recipe titles +
    # descriptions, then we use web search ONLY to attach a real recipe URL.
    # (Search-first produced garbage cards — web-page titles like "… - Facebook"
    # and snippet text instead of an actual recipe name.)
    try:
        ideas = llm_svc.generate_meal_ideas(prefs, fav_names, n=target - len(recipes) + 2)
    except Exception as exc:
        logger.error("LLM meal idea generation failed: %s", exc)
        ideas = []

    for idea in ideas:
        if len(recipes) >= target:
            break
        title = (idea.get("title") or "").strip()
        if not title:
            continue
        description = (idea.get("description") or "").strip()
        query = idea.get("search_query") or f"{title} recipe"
        url = ""
        try:
            results = search_recipes(query, max_results=1)
        except Exception as exc:
            logger.warning("Recipe URL search failed for '%s': %s", title, exc)
            results = []
        if results:
            url = results[0].get("url", "") or ""
            # Keep the LLM's title/description; only borrow a snippet if missing.
            if not description:
                description = results[0].get("description", "") or ""
        if url:
            if url in seen_urls:
                continue
            seen_urls.add(url)
        recipes.append({
            "title": title,
            "url": url,
            "description": description,
            "is_favorite": False,
        })

    # Last-resort fallback: LLM unavailable AND we have nothing but maybe a
    # favorite — pull a couple of raw search hits so the email still delivers.
    if len(recipes) <= (1 if favorites else 0):
        logger.warning("No LLM ideas — falling back to raw web search for meal plan")
        prefs_clause = f" that are {prefs}" if prefs else ""
        for query in (
            f"easy healthy dinner recipe{prefs_clause}",
            f"quick weeknight meal idea{prefs_clause}",
        ):
            if len(recipes) >= target:
                break
            try:
                results = search_recipes(query, max_results=2)
            except Exception:
                results = []
            for r in results:
                url = r.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    recipes.append({
                        "title": r.get("title") or "New Recipe Idea",
                        "url": url,
                        "description": r.get("description", ""),
                        "is_favorite": False,
                    })

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
