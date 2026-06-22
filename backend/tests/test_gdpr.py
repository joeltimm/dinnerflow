"""GDPR data-export + account-deletion tests (routers/account.py)."""
import json

from auth.utils import encrypt_token
from config import get_settings
from routers.account import _delete_user_uploaded_images, _export_user_data
from tests.conftest import seed_user


def _seed_full_user(db, email="gdpr@example.com"):
    """A user with a row in every child table."""
    uid = seed_user(db, email=email)
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO recipes (title, ingredients, instructions, user_id) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            ("Soup", json.dumps(["water"]), json.dumps(["boil"]), uid),
        )
        recipe_id = cur.fetchone()["id"]
        cur.execute(
            "INSERT INTO cooking_log (recipe_id, rating) VALUES (%s, %s)", (recipe_id, 5)
        )
        cur.execute(
            "INSERT INTO shopping_list_items (user_id, item_text) VALUES (%s, %s)",
            (uid, "milk"),
        )
        cur.execute(
            "INSERT INTO user_integrations (user_id, provider, api_token, target_list_name) "
            "VALUES (%s, 'todoist', %s, %s)",
            (uid, encrypt_token("super-secret-todoist-token"), "Groceries"),
        )
        cur.execute(
            "INSERT INTO search_terms (term, user_id) VALUES (%s, %s)", ("pasta", uid)
        )
        cur.execute(
            "INSERT INTO recipe_sync_logs (user_id, recipe_id, ingredients_count) "
            "VALUES (%s, %s, %s)",
            (uid, recipe_id, 1),
        )
    return uid, recipe_id


def test_export_includes_all_sections(db):
    uid, _ = _seed_full_user(db)
    data = _export_user_data(db, uid)
    for key in ("profile", "recipes", "cooking_log", "shopping_list",
                "integrations", "search_terms", "sync_logs"):
        assert key in data
    assert data["recipes"][0]["title"] == "Soup"
    assert len(data["cooking_log"]) == 1


def test_export_excludes_encrypted_token(db):
    uid, _ = _seed_full_user(db)
    data = _export_user_data(db, uid)
    # The integration is reported, but the encrypted token must never leak.
    assert data["integrations"][0]["provider"] == "todoist"
    blob = json.dumps(data, default=str)
    assert "super-secret-todoist-token" not in blob
    assert "api_token" not in data["integrations"][0]


def test_delete_uploaded_images(db, tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "uploads_path", str(tmp_path))
    img = tmp_path / "pic.jpg"
    img.write_bytes(b"\xff\xd8\xff")
    uid = seed_user(db, email="img@example.com")
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO recipes (title, local_image_path, user_id) VALUES (%s, %s, %s)",
            ("Has image", "pic.jpg", uid),
        )
    removed = _delete_user_uploaded_images(db, uid)
    assert removed == 1
    assert not img.exists()


def test_delete_user_cascades_all_children(db):
    """Deleting the user must erase every child row (GDPR Art. 17).

    cooking_log links to the user only via recipe_id; its FK to recipes must
    cascade or this deletion fails with a foreign-key violation.
    """
    uid, recipe_id = _seed_full_user(db, email="erase@example.com")
    with db.cursor() as cur:
        cur.execute("INSERT INTO user_sessions (token, user_id, expires_at) "
                    "VALUES (%s, %s, NOW() + interval '1 day')", ("tok-erase", uid))
        cur.execute("DELETE FROM users WHERE id = %s", (uid,))

        for table, col, val in [
            ("recipes", "user_id", uid),
            ("cooking_log", "recipe_id", recipe_id),
            ("shopping_list_items", "user_id", uid),
            ("user_integrations", "user_id", uid),
            ("search_terms", "user_id", uid),
            ("user_sessions", "user_id", uid),
        ]:
            cur.execute(f"SELECT count(*) AS n FROM {table} WHERE {col} = %s", (val,))
            assert cur.fetchone()["n"] == 0, f"{table} still has rows after user delete"
