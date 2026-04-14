"""
Signed token utilities for email action links and unsubscribe links.

Extracted from routers so that services (e.g. scheduler) can generate tokens
without importing from the router layer.
"""
from fastapi import HTTPException
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import get_settings


# ── Email action tokens (e.g. "Add to My Recipes" links) ────────────────────

def _email_signer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().secret_key, salt="email-select")


def make_email_token(user_id: int) -> str:
    """Create a signed, time-limited token encoding user_id for email links."""
    return _email_signer().dumps(user_id)


def verify_email_token(token: str) -> int:
    """Decode and verify an email action token. Returns user_id or raises HTTPException."""
    max_age = get_settings().email_link_max_age_days * 86400
    try:
        user_id = _email_signer().loads(token, max_age=max_age)
        return int(user_id)
    except SignatureExpired:
        raise HTTPException(
            status_code=400,
            detail=f"Email link has expired ({get_settings().email_link_max_age_days}-day limit)",
        )
    except BadSignature:
        raise HTTPException(status_code=400, detail="Invalid email link")


# ── Unsubscribe tokens ──────────────────────────────────────────────────────

def _unsubscribe_signer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().secret_key, salt="email-unsubscribe")


def make_unsubscribe_token(user_id: int) -> str:
    """Create a signed token for one-click email unsubscribe links."""
    return _unsubscribe_signer().dumps(user_id)


def verify_unsubscribe_token(token: str) -> int:
    """Decode and verify an unsubscribe token. Returns user_id or raises."""
    max_age = get_settings().unsubscribe_link_max_age_days * 86400
    return int(_unsubscribe_signer().loads(token, max_age=max_age))
