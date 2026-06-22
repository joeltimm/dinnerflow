"""
Pytest harness for the Iron Skillet backend.

Strategy
--------
- Tests run against a **dedicated test database** (never the live one). Its name
  is the live DB name + ``_test`` (or whatever ``TEST_DATABASE_URL`` points at).
  Per the project's fast-test preference on the HDD box, point the test DB at a
  tmpfs / ``fsync=off`` Postgres for speed.
- The test DB is created (if missing) and its schema applied once per session.
  Schema source preference: the canonical repo-root ``dinnerflow_schema.sql``
  (available in CI / on the host), else the bundled ``tests/schema.sql`` snapshot
  (always present inside the backend image). Regenerate the snapshot with::

      docker exec dinner-db pg_dump -U dinneruser -d dinnerflow \
          --schema-only --no-owner --no-privileges > backend/tests/schema.sql

- Each test gets a connection wrapped in a transaction that is **rolled back**
  on teardown, so tests are isolated and leave no residue.
- External services (LLM, scraper, search, email, Todoist) are mocked by an
  autouse fixture so tests never touch the network.
"""
import os
from pathlib import Path

import psycopg2
import psycopg2.extras
import pytest

# ── Point the whole app at the test database BEFORE importing config ──────────
# get_settings() is lru_cached and reads env at first call, so the override must
# happen before anything imports it.
_BASE_DB = os.environ.get("DINNER_DB_NAME", "dinnerflow")
_TEST_DB = _BASE_DB if _BASE_DB.endswith("_test") else f"{_BASE_DB}_test"
os.environ["DINNER_DB_NAME"] = _TEST_DB
# Provide harmless fallbacks so settings load even outside the container.
os.environ.setdefault("DINNER_DB_PASSWORD", "postgres")
os.environ.setdefault("FERNET_KEY", "6pJWeXaTkkFaPU__nlYsU3opxkqjU-UFy0ulok0hhMI=")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")

from config import get_settings  # noqa: E402

get_settings.cache_clear()
SETTINGS = get_settings()

import database  # noqa: E402
from auth.utils import create_session_token  # noqa: E402


# ── Test-DB lifecycle ─────────────────────────────────────────────────────────

def _admin_dsn() -> str:
    """DSN to the maintenance ``postgres`` DB for CREATE DATABASE."""
    return (
        f"host={SETTINGS.dinner_db_host} port={SETTINGS.dinner_db_port} "
        f"user={SETTINGS.dinner_db_user} password={SETTINGS.dinner_db_password} "
        f"dbname=postgres"
    )


def _schema_sql() -> str:
    candidates = [
        os.environ.get("SCHEMA_SQL_PATH"),
        # repo-root canonical schema (CI / host runs)
        str(Path(__file__).resolve().parents[2] / "dinnerflow_schema.sql"),
        # bundled snapshot (always in the backend image)
        str(Path(__file__).resolve().parent / "schema.sql"),
    ]
    for path in candidates:
        if path and Path(path).exists():
            raw = Path(path).read_text()
            # Drop psql meta-commands (e.g. \restrict / \unrestrict that newer
            # pg_dump emits) — psycopg2 executes SQL, not the psql client.
            return "\n".join(
                line for line in raw.splitlines() if not line.lstrip().startswith("\\")
            )
    raise RuntimeError("No schema SQL found (looked for dinnerflow_schema.sql / tests/schema.sql)")


@pytest.fixture(scope="session", autouse=True)
def _ensure_test_db():
    """Create the test DB (if absent) and apply the schema once per session."""
    # 1. CREATE DATABASE <test> if it does not exist
    admin = psycopg2.connect(_admin_dsn())
    admin.autocommit = True
    try:
        with admin.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (_TEST_DB,))
            if not cur.fetchone():
                cur.execute(f'CREATE DATABASE "{_TEST_DB}"')
    finally:
        admin.close()

    # 2. Apply schema if the DB looks empty
    conn = psycopg2.connect(SETTINGS.db_dsn)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('public.users')")
            if cur.fetchone()[0] is None:
                cur.execute(_schema_sql())
    finally:
        conn.close()

    # 3. Init the app's pool against the test DB for any get_connection() paths
    if database._pool is None:
        database.init_pool()

    yield


# Data tables truncated between tests for isolation (alembic_version is left alone).
_APP_TABLES = (
    "cooking_log", "recipe_sync_logs", "shopping_list_items", "search_terms",
    "user_integrations", "user_sessions", "recipes", "users",
)


@pytest.fixture
def db():
    """
    An autocommit connection for seeding/asserting. All app tables are truncated
    after each test so endpoints (which use their own pooled connections) and the
    test share the same committed state without cross-connection visibility issues.
    """
    conn = psycopg2.connect(SETTINGS.db_dsn)
    conn.autocommit = True
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    with conn.cursor() as cur:
        # Test DB only — skip per-commit fsync (HDD box). CI uses an fsync=off PG.
        cur.execute("SET synchronous_commit = off")
    try:
        yield conn
    finally:
        # DELETE (children→parents) is far cheaper than TRUNCATE's fsync on this box.
        with conn.cursor() as cur:
            cur.execute(f"DELETE FROM {'; DELETE FROM '.join(_APP_TABLES)}")
        conn.close()


# ── App / HTTP client ─────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """TestClient against the app; endpoints use the pool bound to the test DB."""
    from fastapi.testclient import TestClient

    from main import create_app

    with TestClient(create_app()) as c:
        yield c


@pytest.fixture(autouse=True)
def _clear_session_cache():
    """Session validation caches users for 60s — clear between tests."""
    import dependencies
    with dependencies._cache_lock:
        dependencies._session_cache.clear()
    yield


# ── External-service mocks (no network in tests) ──────────────────────────────

@pytest.fixture(autouse=True)
def mocks(mocker):
    """
    Patch every outbound integration with safe defaults. Tests can override a
    return value via the returned namespace, e.g. ``mocks.extract_recipe.return_value = {...}``.
    """
    ns = type("Mocks", (), {})()
    ns.fetch_and_clean = mocker.patch(
        "services.scraper.fetch_and_clean", return_value="cleaned recipe text"
    )
    ns.extract_recipe = mocker.patch(
        "services.llm.extract_recipe",
        return_value={"ingredients": ["1 egg", "2 cups flour"], "instructions": ["Mix.", "Bake."]},
    )
    ns.generate_meal_ideas = mocker.patch(
        "services.llm.generate_meal_ideas",
        return_value=[{"title": "Test Dish", "description": "Tasty.", "search_query": "test dish recipe"}],
    )
    # Non-zero default vector (cosine distance is undefined for the zero vector).
    import services.llm as _llm_mod
    ns._real_generate_embedding = _llm_mod.generate_embedding  # capture before patching
    ns.generate_embedding = mocker.patch(
        "services.llm.generate_embedding", return_value=[1.0] + [0.0] * 767
    )
    ns.search_recipes = mocker.patch(
        "services.search.search_recipes", return_value=[{"title": "T", "url": "https://x/r"}]
    )
    ns.sync_ingredients = mocker.patch("services.todoist.sync_ingredients", return_value=2)
    ns.send_welcome_email = mocker.patch("services.email.send_welcome_email", return_value=None)
    ns.send_meal_plan_email = mocker.patch(
        "services.email.send_meal_plan_email", return_value=None, create=True
    )
    return ns


# ── Seed helpers ──────────────────────────────────────────────────────────────

def seed_user(conn, email="chef@example.com", *, is_admin=False, full_name="Chef",
              email_consent=False, password_hash="x") -> int:
    """Insert a user and return its id."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (email, password_hash, full_name, is_admin, email_consent) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (email, password_hash, full_name, is_admin, email_consent),
        )
        return cur.fetchone()["id"]


def seed_session(conn, user_id: int) -> str:
    """Create a valid session token for a user and return it."""
    token, _ = create_session_token(conn, user_id)
    return token
