"""
Account management endpoints — data export and deletion.

GET    /api/account/export-data   — download all user data as JSON (GDPR portability)
DELETE /api/account/delete        — permanently delete own account and all data
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from config import get_settings
from database import get_db
from dependencies import get_current_user, invalidate_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/account", tags=["account"])


def _export_user_data(conn, user_id: int) -> dict:
    """
    Gather all data belonging to a user across every table.
    Returns a dict suitable for JSON serialization.
    """
    with conn.cursor() as cur:
        # Profile
        cur.execute(
            "SELECT id, email, full_name, dietary_preferences, created_at "
            "FROM users WHERE id = %s",
            (user_id,),
        )
        profile = cur.fetchone()
        if not profile:
            return {}
        profile = dict(profile)

        # Recipes
        cur.execute(
            "SELECT id, title, source_url, ingredients, instructions, "
            "entry_method, rating, times_cooked, last_cooked, is_favorite, created_at "
            "FROM recipes WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,),
        )
        recipes = [dict(r) for r in cur.fetchall()]

        # Cooking log (join through recipes owned by this user)
        cur.execute(
            "SELECT cl.id, cl.recipe_id, r.title AS recipe_title, "
            "cl.date_cooked, cl.rating, cl.notes, cl.created_at "
            "FROM cooking_log cl "
            "JOIN recipes r ON r.id = cl.recipe_id "
            "WHERE r.user_id = %s ORDER BY cl.date_cooked DESC",
            (user_id,),
        )
        cooking_log = [dict(r) for r in cur.fetchall()]

        # Shopping list
        cur.execute(
            "SELECT id, item_text, recipe_source, is_checked, created_at "
            "FROM shopping_list_items WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,),
        )
        shopping_list = [dict(r) for r in cur.fetchall()]

        # Integrations (exclude encrypted tokens — show provider + list name only)
        cur.execute(
            "SELECT provider, target_list_name "
            "FROM user_integrations WHERE user_id = %s",
            (user_id,),
        )
        integrations = [dict(r) for r in cur.fetchall()]

        # Search terms
        cur.execute(
            "SELECT term, category, last_used_at, created_at "
            "FROM search_terms WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,),
        )
        search_terms = [dict(r) for r in cur.fetchall()]

        # Sync logs
        cur.execute(
            "SELECT recipe_id, ingredients_count, provider, synced_at "
            "FROM recipe_sync_logs WHERE user_id = %s ORDER BY synced_at DESC",
            (user_id,),
        )
        sync_logs = [dict(r) for r in cur.fetchall()]

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
        "recipes": recipes,
        "cooking_log": cooking_log,
        "shopping_list": shopping_list,
        "integrations": integrations,
        "search_terms": search_terms,
        "sync_logs": sync_logs,
    }


def _delete_user_uploaded_images(conn, user_id: int) -> int:
    """Delete all uploaded recipe images for a user. Returns count of files removed."""
    settings = get_settings()
    uploads_dir = Path(settings.uploads_path)
    removed = 0

    with conn.cursor() as cur:
        cur.execute(
            "SELECT local_image_path FROM recipes "
            "WHERE user_id = %s AND local_image_path IS NOT NULL",
            (user_id,),
        )
        for row in cur.fetchall():
            img_path = uploads_dir / Path(row["local_image_path"]).name
            try:
                img_path.unlink(missing_ok=True)
                removed += 1
            except OSError as exc:
                logger.warning("Failed to delete image %s: %s", img_path, exc)

    return removed


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/export-data")
def export_data(conn=Depends(get_db), user=Depends(get_current_user)):
    """
    Export all data belonging to the current user as JSON.
    GDPR Article 20 — Right to data portability.
    """
    data = _export_user_data(conn, user["id"])
    if not data:
        raise HTTPException(status_code=404, detail="User not found")

    return JSONResponse(
        content=json.loads(json.dumps(data, default=str)),
        headers={
            "Content-Disposition": f'attachment; filename="ironskillet_data_{user["id"]}.json"'
        },
    )


class DeleteAccountRequest(BaseModel):
    confirm: bool = False


@router.delete("/delete", status_code=status.HTTP_200_OK)
def delete_account(
    body: DeleteAccountRequest,
    response: Response,
    conn=Depends(get_db),
    user=Depends(get_current_user),
    session_token: Optional[str] = Cookie(default=None),
):
    """
    Permanently delete the current user's account and all associated data.
    Requires {"confirm": true} in the request body as a safety check.

    GDPR Article 17 — Right to erasure.

    Deletion order:
    1. Export data snapshot (logged, not returned)
    2. Delete uploaded image files from disk
    3. DELETE FROM users WHERE id = ? (CASCADE handles all child rows)
    4. Invalidate session, clear cookie
    """
    if not body.confirm:
        raise HTTPException(
            status_code=400,
            detail="Account deletion requires confirm=true",
        )

    user_id = user["id"]
    email = user["email"]

    logger.info("Account deletion requested by user %d (%s)", user_id, email)

    # 1. Delete uploaded images before the recipe rows are cascaded away
    images_removed = _delete_user_uploaded_images(conn, user_id)
    logger.info("Removed %d uploaded image(s) for user %d", images_removed, user_id)

    # 2. Delete user row — CASCADE handles all child tables
    with conn.cursor() as cur:
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")

    logger.info("User %d (%s) permanently deleted", user_id, email)

    # 3. Invalidate session
    if session_token:
        invalidate_session(session_token)
    response.delete_cookie("session_token")

    return {
        "deleted": True,
        "user_id": user_id,
        "email": email,
        "images_removed": images_removed,
    }
