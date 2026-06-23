"""
Shopping list endpoints.

GET    /api/shopping          — list items for current user
POST   /api/shopping          — add an item
PUT    /api/shopping/{id}     — toggle checked state
DELETE /api/shopping/{id}     — delete a single item
DELETE /api/shopping/checked  — clear all checked items
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from database import get_db
from dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/shopping", tags=["shopping"])


class ShoppingItemCreate(BaseModel):
    item_text: str = Field(..., max_length=500)
    recipe_source: str | None = Field(default=None, max_length=500)


@router.get("")
def list_items(conn=Depends(get_db), user=Depends(get_current_user)):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, item_text, recipe_source, is_checked, created_at
            FROM shopping_list_items
            WHERE user_id = %s
            ORDER BY is_checked ASC, created_at DESC
            """,
            (user["id"],),
        )
        return [dict(r) for r in cur.fetchall()]


@router.post("", status_code=status.HTTP_201_CREATED)
def add_item(body: ShoppingItemCreate, conn=Depends(get_db), user=Depends(get_current_user)):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO shopping_list_items (user_id, item_text, recipe_source)
            VALUES (%s, %s, %s)
            RETURNING id, item_text, recipe_source, is_checked, created_at
            """,
            (user["id"], body.item_text, body.recipe_source),
        )
        item = dict(cur.fetchone())
    from services import metrics
    metrics.record_shopping_add("recipe" if body.recipe_source else "manual")
    return item


@router.post("/from-recipe/{recipe_id}", status_code=status.HTTP_201_CREATED)
def add_from_recipe(recipe_id: int, conn=Depends(get_db), user=Depends(get_current_user)):
    """
    Add all of a recipe's ingredients to the shopping list in one click.

    Tags each item with recipe_source = the recipe title, and skips ingredients
    already present for that same recipe (case-insensitive) so re-adding is safe.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT title, ingredients FROM recipes WHERE id = %s AND user_id = %s",
            (recipe_id, user["id"]),
        )
        recipe = cur.fetchone()
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")

        source = recipe["title"]
        ingredients = recipe["ingredients"] or []  # jsonb → list[str]

        cur.execute(
            "SELECT lower(item_text) AS t FROM shopping_list_items "
            "WHERE user_id = %s AND recipe_source = %s",
            (user["id"], source),
        )
        existing = {r["t"] for r in cur.fetchall()}

        added = []
        for raw in ingredients:
            item = (raw or "").strip()
            if not item or item.lower() in existing:
                continue
            cur.execute(
                "INSERT INTO shopping_list_items (user_id, item_text, recipe_source) "
                "VALUES (%s, %s, %s) "
                "RETURNING id, item_text, recipe_source, is_checked, created_at",
                (user["id"], item, source),
            )
            added.append(dict(cur.fetchone()))
            existing.add(item.lower())

    if added:
        from services import metrics
        metrics.record_shopping_add("recipe", len(added))
    return {"added": added, "count": len(added), "recipe_source": source}


@router.delete("/checked", status_code=status.HTTP_204_NO_CONTENT)
def clear_checked(conn=Depends(get_db), user=Depends(get_current_user)):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM shopping_list_items WHERE user_id = %s AND is_checked = true",
            (user["id"],),
        )


@router.put("/{item_id}")
def toggle_item(item_id: int, conn=Depends(get_db), user=Depends(get_current_user)):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE shopping_list_items
            SET is_checked = NOT is_checked
            WHERE id = %s AND user_id = %s
            RETURNING id, item_text, recipe_source, is_checked, created_at
            """,
            (item_id, user["id"]),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")
    return dict(row)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, conn=Depends(get_db), user=Depends(get_current_user)):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM shopping_list_items WHERE id = %s AND user_id = %s",
            (item_id, user["id"]),
        )
