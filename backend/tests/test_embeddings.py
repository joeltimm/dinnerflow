"""Phase 2: embeddings, semantic search, and duplicate detection."""
from routers.chef import _scrape_and_save_recipe
from services import llm
from tests.conftest import seed_session, seed_user


def vec(i: int) -> list[float]:
    """A 768-dim one-hot unit vector (orthogonal vectors → cosine distance 1)."""
    v = [0.0] * 768
    v[i] = 1.0
    return v


def test_recipe_embedding_text_combines_fields():
    text = llm.recipe_embedding_text("Soup", ["water", "salt"], ["boil it"])
    assert "Soup" in text and "water" in text and "boil it" in text


def test_to_pgvector_format():
    assert llm.to_pgvector([1.0, 2.5]) == "[1.0,2.5]"


def test_generate_embedding_parses_client_response(monkeypatch, mocks):
    class _Resp:
        data = [type("D", (), {"embedding": [0.1] * 768})()]

    class _Client:
        class embeddings:
            @staticmethod
            def create(**kwargs):
                return _Resp

    monkeypatch.setattr(llm, "_client", lambda timeout=None: _Client)
    # generate_embedding is mocked globally; exercise the real implementation here.
    out = mocks._real_generate_embedding("hello")
    assert len(out) == 768 and out[0] == 0.1


def test_semantic_search_orders_by_similarity(client, db, mocks):
    uid = seed_user(db, email="search@example.com")
    token = seed_session(db, uid)
    for title, v in [("Apple Pie", vec(0)), ("Beef Stew", vec(1))]:
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO recipes (title, user_id, embedding) VALUES (%s, %s, %s::vector)",
                (title, uid, llm.to_pgvector(v)),
            )
    mocks.generate_embedding.return_value = vec(0)  # query closest to Apple Pie
    r = client.get("/api/recipes/search?q=dessert", headers={"Cookie": f"session_token={token}"})
    assert r.status_code == 200, r.text
    titles = [row["title"] for row in r.json()]
    assert titles[0] == "Apple Pie"


def test_search_omits_unembedded_recipes(client, db, mocks):
    uid = seed_user(db, email="search2@example.com")
    token = seed_session(db, uid)
    with db.cursor() as cur:
        cur.execute("INSERT INTO recipes (title, user_id) VALUES (%s, %s)", ("No Embedding", uid))
    mocks.generate_embedding.return_value = vec(0)
    r = client.get("/api/recipes/search?q=anything", headers={"Cookie": f"session_token={token}"})
    assert r.status_code == 200
    assert r.json() == []


def test_import_detects_duplicate(db, mocks):
    uid = seed_user(db, email="dup2@example.com")
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO recipes (title, user_id, embedding) VALUES (%s, %s, %s::vector) RETURNING id",
            ("Classic Pancakes", uid, llm.to_pgvector(vec(5))),
        )
        existing_id = cur.fetchone()["id"]

    mocks.generate_embedding.return_value = vec(5)  # identical → duplicate
    result = _scrape_and_save_recipe(db, uid, "Pancakes", "https://example.com/p", "email_select")
    assert result["duplicate_of"] is not None
    assert result["duplicate_of"]["id"] == existing_id


def test_import_unique_recipe_not_flagged(db, mocks):
    uid = seed_user(db, email="uniq@example.com")
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO recipes (title, user_id, embedding) VALUES (%s, %s, %s::vector)",
            ("Tacos", uid, llm.to_pgvector(vec(10))),
        )
    mocks.generate_embedding.return_value = vec(20)  # orthogonal → distance 1, not a dup
    result = _scrape_and_save_recipe(db, uid, "Sushi", "https://example.com/s", "email_select")
    assert result["duplicate_of"] is None
