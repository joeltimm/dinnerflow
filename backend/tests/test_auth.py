"""Auth + session lifecycle tests (auth/router.py, auth/utils.py, dependencies.py)."""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from auth.utils import hash_password
from dependencies import require_admin
from tests.conftest import seed_user


def test_login_then_me(client, db):
    seed_user(db, email="login@example.com", password_hash=hash_password("secret"))
    resp = client.post("/api/auth/login", json={"email": "login@example.com", "password": "secret"})
    assert resp.status_code == 200, resp.text
    token = resp.cookies.get("session_token")
    assert token

    # Send the session cookie explicitly — exercises get_current_user against the
    # committed session row (avoids httpx jar quirks around the cookie expiry fmt).
    me = client.get("/api/auth/me", headers={"Cookie": f"session_token={token}"})
    assert me.status_code == 200, me.text
    assert me.json()["email"] == "login@example.com"


def test_login_wrong_password_rejected(client, db):
    seed_user(db, email="login2@example.com", password_hash=hash_password("secret"))
    resp = client.post("/api/auth/login", json={"email": "login2@example.com", "password": "nope"})
    assert resp.status_code == 401


def test_me_requires_authentication(client):
    assert client.get("/api/auth/me").status_code == 401


def test_expired_session_rejected(client, db):
    uid = seed_user(db, email="expired@example.com")
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO user_sessions (token, user_id, expires_at) VALUES (%s, %s, %s)",
            ("expired-token", uid, datetime.now(timezone.utc) - timedelta(days=1)),
        )
    client.cookies.set("session_token", "expired-token")
    assert client.get("/api/auth/me").status_code == 401


def test_require_admin_blocks_non_admin():
    with pytest.raises(HTTPException) as exc:
        require_admin({"id": 1, "is_admin": False})
    assert exc.value.status_code == 403


def test_require_admin_allows_admin():
    user = {"id": 1, "is_admin": True}
    assert require_admin(user) is user
