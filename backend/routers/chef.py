"""
Chef endpoints — replaces all n8n AI/scraping workflows.

POST /api/chef/instant-ideas         — generate AI meal suggestions (Tavily + LLM)
POST /api/chef/cook                  — scrape URL, extract recipe via LLM, save to DB
POST /api/chef/email-plan            — trigger meal plan email for current user
GET  /api/chef/select-from-email     — handle 'Add to My Recipes' click from email
"""
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import escape

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from services.search import search_recipes

from auth.tokens import verify_email_token
from auth.utils import decrypt_token
from config import get_settings
from database import get_db
from dependencies import get_current_user
from limiter import limiter
from services import llm as llm_svc
from services import scraper as scraper_svc
from services import todoist as todoist_svc
from services.llm import LLMUnavailable

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chef", tags=["chef"])


# ── Todoist helper ────────────────────────────────────────────────────────────

def _get_todoist_config(conn, user_id: int) -> tuple[str | None, str | None]:
    """
    Returns (decrypted_token, project_id) for user's Todoist integration,
    or (None, None) if not configured.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT api_token, target_list_id FROM user_integrations "
            "WHERE user_id = %s AND provider = 'todoist'",
            (user_id,),
        )
        row = cur.fetchone()

    if not row or not row["api_token"]:
        return None, None

    try:
        plain_token = decrypt_token(row["api_token"])
        return plain_token, row["target_list_id"]
    except Exception:
        logger.warning("Failed to decrypt Todoist token for user %d", user_id)
        return None, None


# ── Request models ────────────────────────────────────────────────────────────

class CookRequest(BaseModel):
    url: str
    title: str | None = None


# ── Shared recipe-save helper ─────────────────────────────────────────────────

def _scrape_and_save_recipe(
    conn, user_id: int, title: str, url: str, entry_method: str,
    llm_timeout: float | None = None,
) -> dict:
    """
    Scrape url → extract via LLM → save to DB → sync Todoist → log metrics.
    Returns dict with recipe_id, ingredients, instructions, todoist_synced.
    Raises on scrape/LLM failure; Todoist errors are logged and swallowed.

    ``llm_timeout`` is forwarded to the LLM extraction — request-path callers
    (e.g. /cook) pass a short value to fail fast; the Celery task leaves it None.
    """
    cleaned_text = scraper_svc.fetch_and_clean(url)
    extracted = llm_svc.extract_recipe(cleaned_text, timeout=llm_timeout)
    ingredients = extracted.get("ingredients", [])
    instructions = extracted.get("instructions", [])

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO recipes
              (title, source_url, ingredients, instructions, entry_method, user_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (title, url, json.dumps(ingredients), json.dumps(instructions), entry_method, user_id),
        )
        recipe_id = cur.fetchone()["id"]

    todoist_token, todoist_project = _get_todoist_config(conn, user_id)
    todoist_synced = 0
    todoist_error = False
    if todoist_token and todoist_project:
        try:
            todoist_synced = todoist_svc.sync_ingredients(
                todoist_token, todoist_project, ingredients, title
            )
        except Exception as exc:
            logger.warning("Todoist sync failed for recipe %d: %s", recipe_id, exc)
            todoist_error = True

    if todoist_token and todoist_project:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO recipe_sync_logs
                  (user_id, recipe_id, ingredients_count, provider)
                VALUES (%s, %s, %s, 'todoist')
                """,
                (user_id, recipe_id, todoist_synced),
            )

    return {
        "recipe_id": recipe_id,
        "ingredients": ingredients,
        "instructions": instructions,
        "todoist_synced": todoist_synced,
        "todoist_error": todoist_error,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/instant-ideas")
@limiter.limit("5/minute")
def instant_ideas(request: Request, conn=Depends(get_db), user=Depends(get_current_user)):
    """
    Generate AI meal suggestions based on user preferences + favorites.

    Flow (replaces n8n 'instant-ideas' webhook):
    1. Load user prefs + favorite recipe titles from DB
    2. Ask LLM to generate N meal ideas with search queries
    3. Use Tavily to find real recipe URLs for each idea
    4. Return merged list
    """
    settings = get_settings()

    # Load user favorites
    with conn.cursor() as cur:
        cur.execute(
            "SELECT title FROM recipes WHERE user_id = %s AND is_favorite = true LIMIT 20",
            (user["id"],),
        )
        favorites = [r["title"] for r in cur.fetchall()]

    prefs = user.get("dietary_preferences") or ""

    # Generate ideas via LLM (short request-path timeout so a stalled LLM
    # fails fast with a friendly message instead of hanging the request).
    try:
        ideas = llm_svc.generate_meal_ideas(
            prefs, favorites, n=10, timeout=settings.llm_request_timeout
        )
    except LLMUnavailable:
        raise HTTPException(
            status_code=503,
            detail="The AI chef is busy right now — please try again in a moment.",
        )
    except Exception as exc:
        logger.error("instant-ideas LLM error for user %d: %s", user["id"], exc)
        raise HTTPException(status_code=502, detail="The AI returned an unexpected response.")

    # Enrich ideas with real recipe URLs in parallel.
    # search_recipes() tries Tavily first, falls back to DuckDuckGo automatically
    # if Tavily is unconfigured or returns an error (quota exceeded, 429, etc.).
    def _enrich(idx: int, idea: dict) -> tuple[int, list[dict]]:
        query = idea.get("search_query") or f"{idea['title']} recipe"
        return idx, search_recipes(query, max_results=1)

    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(_enrich, i, idea): i for i, idea in enumerate(ideas)}
        for fut in as_completed(futures):
            idx, results = fut.result()
            if results:
                best = results[0]
                ideas[idx]["url"] = best["url"]
                if not ideas[idx].get("description"):
                    ideas[idx]["description"] = best["description"]
            else:
                ideas[idx]["url"] = ""

    return ideas


@router.post("/cook")
@limiter.limit("10/minute")
def cook_recipe(request: Request, body: CookRequest, conn=Depends(get_db), user=Depends(get_current_user)):
    """
    Scrape a recipe URL, extract ingredients/instructions via LLM,
    save to DB, and sync to Todoist if configured.

    Replaces the n8n 'Cook Tonight Workflow' and 'Selection Ingestor'.
    """
    settings = get_settings()
    title = body.title or "Untitled Recipe"
    try:
        saved = _scrape_and_save_recipe(
            conn, user["id"], title, body.url, "instant_chef",
            llm_timeout=settings.llm_request_timeout,
        )
    except LLMUnavailable:
        raise HTTPException(
            status_code=503,
            detail="The AI chef is busy right now — please try again in a moment.",
        )
    except Exception as exc:
        logger.error("cook failed for user %d: %s", user["id"], exc)
        raise HTTPException(status_code=502, detail="Failed to fetch or parse recipe")

    return {"title": title, **saved}


@router.post("/email-plan")
@limiter.limit("3/minute")
def trigger_email_plan(request: Request, conn=Depends(get_db), user=Depends(get_current_user)):
    """
    Manually trigger a meal plan email for the current user.
    (Celery Beat also triggers this daily at 10:30 AM, sending only to users
    whose email_days include that weekday.)

    Replaces the n8n 'Ironskillet' workflow's webhook trigger path.
    """
    from tasks import send_meal_plan_for_user
    try:
        send_meal_plan_for_user.delay(user["id"], user["email"], user.get("full_name", "Chef"))
    except Exception as exc:
        logger.error("Failed to enqueue meal plan: %s", exc)
        raise HTTPException(status_code=503, detail="Task queue unavailable — try again shortly")
    return {"ok": True, "message": f"Meal plan queued for {user['email']}"}


@router.get("/select-from-email", response_class=HTMLResponse)
@limiter.limit("10/minute")
def select_from_email(
    request: Request,
    token: str = Query(...),
    title: str = Query(...),
    url: str = Query(""),
    conn=Depends(get_db),
):
    """
    Handles 'Add to My Recipes' clicks from meal plan emails.
    Replaces the n8n 'Selection Ingestor' (/webhook/select).

    Uses a HMAC-signed token (no login required) to identify the user. The slow
    scrape → LLM extract → save → Todoist sync runs in a background Celery task,
    so the click returns an instant confirmation instead of hanging on the request.
    """
    # Verify signed token from email link (raises on tampered/expired links)
    user_id = verify_email_token(token)
    app_url = get_settings().app_base_url

    # DOCTYPE + charset so accented recipe titles (e.g. "Crêpes") render correctly.
    head = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1"></head>'
    )

    # The signed token proves the user existed when the email was sent, but an
    # account can be deleted within the 7-day token window — fail cleanly.
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM users WHERE id = %s", (user_id,))
        if not cur.fetchone():
            return HTMLResponse(f"""
            {head}
            <body style="font-family:-apple-system,sans-serif;max-width:500px;margin:60px auto;text-align:center;">
              <h2>Account not found</h2>
              <p style="color:#666;">This account no longer exists.</p>
              <a href="{escape(app_url)}">← Back to Iron Skillet</a>
            </body></html>
            """, status_code=404)

    if not url:
        return HTMLResponse(f"""
        {head}
        <body style="font-family:-apple-system,sans-serif;max-width:500px;margin:60px auto;text-align:center;">
          <h2>⚠️ No recipe link</h2>
          <p style="color:#666;">This suggestion didn't include a source link to import.</p>
          <a href="{escape(app_url)}">← Back to Iron Skillet</a>
        </body></html>
        """)

    # Hand the slow work to a worker and return immediately.
    from tasks import scrape_and_save_recipe
    scrape_and_save_recipe.delay(user_id, title, url)

    return HTMLResponse(f"""
    {head}
    <body style="font-family:-apple-system,sans-serif;max-width:500px;margin:60px auto;text-align:center;
                 background:#f9f9f9;padding:40px;">
      <div style="background:#fff;border-radius:12px;padding:40px;box-shadow:0 2px 8px rgba(0,0,0,.1);">
        <div style="font-size:48px;margin-bottom:16px;">🍳</div>
        <h2 style="color:#1a1a2e;margin:0 0 12px;">Adding your recipe…</h2>
        <p style="color:#666;margin:0 0 8px;">
          <strong>{escape(title)}</strong> is being saved to your recipes now. It'll appear in
          a moment — we're fetching the page and extracting the ingredients
          (and syncing to Todoist if you have it connected).
        </p>
        <a href="{escape(app_url)}"
           style="display:inline-block;margin-top:24px;background:#1a1a2e;color:#e2b96f;
                  padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:700;">
          View in Iron Skillet →
        </a>
      </div>
    </body></html>
    """)
