"""Phase 3: add a recipe's ingredients to the shopping list."""
import json

from tests.conftest import seed_session, seed_user


def _seed_recipe(db, uid, title, ingredients):
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO recipes (title, ingredients, user_id) VALUES (%s, %s, %s) RETURNING id",
            (title, json.dumps(ingredients), uid),
        )
        return cur.fetchone()["id"]


def test_add_from_recipe(client, db):
    uid = seed_user(db, email="shop@example.com")
    token = seed_session(db, uid)
    rid = _seed_recipe(db, uid, "Omelette", ["2 eggs", "butter", "salt"])

    r = client.post(f"/api/shopping/from-recipe/{rid}", headers={"Cookie": f"session_token={token}"})
    assert r.status_code == 201, r.text
    assert r.json()["count"] == 3

    with db.cursor() as cur:
        cur.execute(
            "SELECT item_text, recipe_source FROM shopping_list_items WHERE user_id = %s", (uid,)
        )
        rows = cur.fetchall()
    assert {x["item_text"] for x in rows} == {"2 eggs", "butter", "salt"}
    assert all(x["recipe_source"] == "Omelette" for x in rows)


def test_add_from_recipe_skips_duplicates(client, db):
    uid = seed_user(db, email="shop2@example.com")
    token = seed_session(db, uid)
    rid = _seed_recipe(db, uid, "Toast", ["bread", "butter"])
    hdr = {"Cookie": f"session_token={token}"}

    assert client.post(f"/api/shopping/from-recipe/{rid}", headers=hdr).json()["count"] == 2
    # Second add is a no-op (same recipe_source, same items).
    assert client.post(f"/api/shopping/from-recipe/{rid}", headers=hdr).json()["count"] == 0


def test_add_from_recipe_rejects_other_users_recipe(client, db):
    owner = seed_user(db, email="owner@example.com")
    rid = _seed_recipe(db, owner, "Secret Sauce", ["mystery"])
    intruder = seed_user(db, email="intruder@example.com")
    token = seed_session(db, intruder)

    r = client.post(f"/api/shopping/from-recipe/{rid}", headers={"Cookie": f"session_token={token}"})
    assert r.status_code == 404
