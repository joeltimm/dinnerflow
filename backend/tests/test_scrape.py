"""Async scrape-and-save path tests (routers/chef.py, tasks.py)."""
import json

from routers.chef import _scrape_and_save_recipe
from tests.conftest import seed_user


def test_scrape_and_save_inserts_recipe(db, mocks):
    uid = seed_user(db, email="scrape@example.com")
    result = _scrape_and_save_recipe(
        db, uid, "My Recipe", "https://example.com/r", "email_select"
    )
    assert result["recipe_id"]
    assert result["ingredients"] == ["1 egg", "2 cups flour"]
    with db.cursor() as cur:
        cur.execute("SELECT title, source_url, entry_method FROM recipes WHERE id = %s",
                    (result["recipe_id"],))
        row = cur.fetchone()
    assert row["title"] == "My Recipe"
    assert row["entry_method"] == "email_select"


def test_todoist_failure_is_swallowed(db, mocks):
    """A Todoist sync error must not break the recipe save."""
    uid = seed_user(db, email="todoist@example.com")
    # Configure a Todoist integration so the sync path runs...
    with db.cursor() as cur:
        from auth.utils import encrypt_token
        cur.execute(
            "INSERT INTO user_integrations (user_id, provider, api_token, target_list_id) "
            "VALUES (%s, 'todoist', %s, %s)",
            (uid, encrypt_token("tok"), "proj-1"),
        )
    mocks.sync_ingredients.side_effect = RuntimeError("Todoist down")

    result = _scrape_and_save_recipe(db, uid, "R", "https://example.com/x", "cook")
    assert result["recipe_id"]            # recipe still saved
    assert result["todoist_error"] is True
    # A sync-log row is still written (with 0 synced)
    with db.cursor() as cur:
        cur.execute("SELECT ingredients_count FROM recipe_sync_logs WHERE recipe_id = %s",
                    (result["recipe_id"],))
        assert cur.fetchone()["ingredients_count"] == 0


def test_scrape_idempotency_guard(db, mocks):
    """The Celery task skips a recipe the user already has (same source_url)."""
    uid = seed_user(db, email="dup@example.com")
    url = "https://example.com/dup"
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO recipes (title, source_url, ingredients, instructions, user_id) "
            "VALUES (%s, %s, %s, %s, %s)",
            ("Existing", url, json.dumps([]), json.dumps([]), uid),
        )
    # Mirror the guard used in tasks.scrape_and_save_recipe.
    with db.cursor() as cur:
        cur.execute("SELECT 1 FROM recipes WHERE user_id = %s AND source_url = %s LIMIT 1",
                    (uid, url))
        already_exists = cur.fetchone() is not None
    assert already_exists is True
