"""
Recipe CRUD endpoints.

GET    /api/recipes           — list all recipes for current user
POST   /api/recipes           — add a recipe (manual entry)
GET    /api/recipes/{id}      — get single recipe
PUT    /api/recipes/{id}      — update recipe fields
DELETE /api/recipes/{id}      — delete recipe
POST   /api/recipes/{id}/cook — log a cook session (updates last_cooked, times_cooked, rating)
PUT    /api/recipes/{id}/rating   — update star rating
PUT    /api/recipes/{id}/favorite — toggle is_favorite
POST   /api/recipes/{id}/image    — upload / replace recipe image
"""
import json
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field
from PIL import Image
import io

from config import get_settings
from database import get_db
from dependencies import get_current_user
from limiter import limiter
from services import llm as llm_svc
from services.llm import LLMUnavailable

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/recipes", tags=["recipes"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _own_recipe(cur, recipe_id: int, user_id: int) -> dict:
    """Fetch a recipe and verify it belongs to user_id. Raises 404 if not found."""
    cur.execute(
        "SELECT * FROM recipes WHERE id = %s AND user_id = %s",
        (recipe_id, user_id),
    )
    r = cur.fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return dict(r)


def _enqueue_embedding(recipe_id: int) -> None:
    """Schedule (re)computation of a recipe's embedding off the request path."""
    try:
        from tasks import embed_recipe
        embed_recipe.delay(recipe_id)
    except Exception as exc:  # broker down etc. — never block the write
        logger.warning("Could not enqueue embedding for recipe %d: %s", recipe_id, exc)


def query_similar(
    cur, user_id: int, vector_literal: str, *,
    limit: int = 20, exclude_id: int | None = None, max_distance: float | None = None,
) -> list[dict]:
    """
    Nearest recipes for a user by cosine distance (pgvector ``<=>``). Only rows
    that already have an embedding are considered. Used by semantic search and by
    duplicate detection on import.
    """
    sql = [
        "SELECT id, title, source_url, local_image_path, rating, is_favorite,",
        "       embedding <=> %s::vector AS distance",
        "FROM recipes",
        "WHERE user_id = %s AND embedding IS NOT NULL",
    ]
    params: list = [vector_literal, user_id]
    if exclude_id is not None:
        sql.append("AND id <> %s")
        params.append(exclude_id)
    sql.append("ORDER BY distance ASC LIMIT %s")
    params.append(limit)
    cur.execute("\n".join(sql), params)
    rows = [dict(r) for r in cur.fetchall()]
    if max_distance is not None:
        rows = [r for r in rows if r["distance"] <= max_distance]
    return rows


# ── Request models ────────────────────────────────────────────────────────────

MAX_IMAGE_SIZE = get_settings().max_image_size_bytes


class RecipeCreate(BaseModel):
    title: str = Field(..., max_length=500)
    source_url: str | None = Field(default=None, max_length=2000)
    ingredients: list[str] = Field(default=[], max_length=500)
    instructions: list[str] = Field(default=[], max_length=500)
    full_text_content: str | None = Field(default=None, max_length=100_000)
    entry_method: str = Field(default="manual", max_length=50)


class RecipeUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    source_url: str | None = Field(default=None, max_length=2000)
    ingredients: list[str] | None = Field(default=None, max_length=500)
    instructions: list[str] | None = Field(default=None, max_length=500)
    full_text_content: str | None = Field(default=None, max_length=100_000)


class CookLog(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = Field(default=None, max_length=2000)


class RatingUpdate(BaseModel):
    rating: float = Field(..., ge=0, le=5)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
def list_recipes(conn=Depends(get_db), user=Depends(get_current_user)):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, title, source_url, local_image_path, rating,
                   times_cooked, last_cooked, is_favorite, created_at, entry_method
            FROM recipes
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 500
            """,
            (user["id"],),
        )
        return [dict(r) for r in cur.fetchall()]


@router.post("", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def create_recipe(request: Request, body: RecipeCreate, conn=Depends(get_db), user=Depends(get_current_user)):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO recipes
              (title, source_url, ingredients, instructions, full_text_content,
               entry_method, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                body.title,
                body.source_url,
                json.dumps(body.ingredients),
                json.dumps(body.instructions),
                body.full_text_content,
                body.entry_method,
                user["id"],
            ),
        )
        created = dict(cur.fetchone())
    _enqueue_embedding(created["id"])
    return created


@router.get("/search")
@limiter.limit("30/minute")
def semantic_search(
    request: Request,
    q: str,
    conn=Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Natural-language recipe search over the user's cookbook. Embeds the query and
    returns the closest recipes by cosine distance. Recipes not yet embedded are
    omitted (their embedding is computed asynchronously on save).
    """
    query = q.strip()
    if not query:
        return []
    try:
        vector = llm_svc.to_pgvector(llm_svc.generate_embedding(query))
    except LLMUnavailable:
        raise HTTPException(
            status_code=503, detail="Search is temporarily unavailable — try again shortly."
        )
    with conn.cursor() as cur:
        return query_similar(cur, user["id"], vector, limit=20)


@router.get("/{recipe_id}")
def get_recipe(recipe_id: int, conn=Depends(get_db), user=Depends(get_current_user)):
    with conn.cursor() as cur:
        return _own_recipe(cur, recipe_id, user["id"])


@router.get("/{recipe_id}/history")
def get_recipe_history(recipe_id: int, conn=Depends(get_db), user=Depends(get_current_user)):
    with conn.cursor() as cur:
        _own_recipe(cur, recipe_id, user["id"])  # ownership check
        cur.execute(
            """
            SELECT id, date_cooked, rating, notes, created_at
            FROM cooking_log
            WHERE recipe_id = %s
            ORDER BY date_cooked DESC
            LIMIT 50
            """,
            (recipe_id,),
        )
        return [dict(r) for r in cur.fetchall()]


@router.put("/{recipe_id}")
def update_recipe(
    recipe_id: int,
    body: RecipeUpdate,
    conn=Depends(get_db),
    user=Depends(get_current_user),
):
    with conn.cursor() as cur:
        _own_recipe(cur, recipe_id, user["id"])  # ownership check

        updates = {}
        if body.title is not None:
            updates["title"] = body.title
        if body.source_url is not None:
            updates["source_url"] = body.source_url
        if body.ingredients is not None:
            updates["ingredients"] = json.dumps(body.ingredients)
        if body.instructions is not None:
            updates["instructions"] = json.dumps(body.instructions)
        if body.full_text_content is not None:
            updates["full_text_content"] = body.full_text_content

        if not updates:
            return {"ok": True}

        set_clause = ", ".join(f"{k} = %s" for k in updates)
        cur.execute(
            f"UPDATE recipes SET {set_clause} WHERE id = %s AND user_id = %s RETURNING *",
            (*updates.values(), recipe_id, user["id"]),
        )
        updated = dict(cur.fetchone())

    # Re-embed only when the semantically meaningful fields changed.
    if updates.keys() & {"title", "ingredients", "instructions"}:
        _enqueue_embedding(recipe_id)
    return updated


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe_id: int, conn=Depends(get_db), user=Depends(get_current_user)):
    with conn.cursor() as cur:
        recipe = _own_recipe(cur, recipe_id, user["id"])

        # Delete image file if present
        if recipe.get("local_image_path"):
            img_path = Path(get_settings().uploads_path) / Path(recipe["local_image_path"]).name
            img_path.unlink(missing_ok=True)

        cur.execute(
            "DELETE FROM recipes WHERE id = %s AND user_id = %s",
            (recipe_id, user["id"]),
        )


@router.post("/{recipe_id}/cook")
def log_cook(
    recipe_id: int,
    body: CookLog,
    conn=Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Record that the user cooked this recipe today.
    - Increments times_cooked
    - Sets last_cooked = NOW()
    - Updates rating if provided
    - Inserts a row into cooking_log
    """
    with conn.cursor() as cur:
        _own_recipe(cur, recipe_id, user["id"])

        if body.rating is not None:
            cur.execute(
                """
                UPDATE recipes
                SET times_cooked = times_cooked + 1,
                    last_cooked  = NOW(),
                    rating       = %s
                WHERE id = %s AND user_id = %s
                """,
                (body.rating, recipe_id, user["id"]),
            )
        else:
            cur.execute(
                """
                UPDATE recipes
                SET times_cooked = times_cooked + 1,
                    last_cooked  = NOW()
                WHERE id = %s AND user_id = %s
                """,
                (recipe_id, user["id"]),
            )

        cur.execute(
            "INSERT INTO cooking_log (recipe_id, rating, notes) VALUES (%s, %s, %s)",
            (recipe_id, body.rating, body.notes),
        )

    return {"ok": True}


@router.put("/{recipe_id}/rating")
def update_rating(
    recipe_id: int,
    body: RatingUpdate,
    conn=Depends(get_db),
    user=Depends(get_current_user),
):
    with conn.cursor() as cur:
        _own_recipe(cur, recipe_id, user["id"])
        cur.execute(
            "UPDATE recipes SET rating = %s WHERE id = %s AND user_id = %s",
            (body.rating, recipe_id, user["id"]),
        )
    return {"ok": True}


@router.put("/{recipe_id}/favorite")
def toggle_favorite(
    recipe_id: int,
    conn=Depends(get_db),
    user=Depends(get_current_user),
):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE recipes
            SET is_favorite = NOT is_favorite
            WHERE id = %s AND user_id = %s
            RETURNING is_favorite
            """,
            (recipe_id, user["id"]),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Recipe not found")
    return {"is_favorite": row["is_favorite"]}


@router.post("/{recipe_id}/image")
async def upload_image(
    recipe_id: int,
    file: UploadFile = File(...),
    conn=Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Process and store a recipe image.
    - Center-crops to square
    - Resizes to 800×800 px
    - Saves as JPEG (quality 85)

    Mirrors ironskillet/ui/pages/recipes.py image-processing logic.
    """
    with conn.cursor() as cur:
        old = _own_recipe(cur, recipe_id, user["id"])

    settings = get_settings()
    uploads_dir = Path(settings.uploads_path)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Remove old image if it exists
    if old.get("local_image_path"):
        old_file = uploads_dir / Path(old["local_image_path"]).name
        old_file.unlink(missing_ok=True)

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="Image exceeds 10 MB limit")
    try:
        img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="File is not a valid image")

    # Center-crop to square
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    size = get_settings().image_resize_px
    img = img.resize((size, size), Image.LANCZOS)

    filename = f"{uuid.uuid4()}.jpg"
    save_path = uploads_dir / filename
    img.save(save_path, "JPEG", quality=get_settings().image_quality)

    # Store relative path in DB (served as /uploads/<filename>)
    rel_path = f"/uploads/{filename}"
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE recipes SET local_image_path = %s WHERE id = %s AND user_id = %s",
            (rel_path, recipe_id, user["id"]),
        )

    return {"image_path": rel_path}
