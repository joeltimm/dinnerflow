"""Unit tests for signed email-action and unsubscribe tokens (auth/tokens.py)."""
import pytest
from fastapi import HTTPException

from auth import tokens
from config import get_settings


def test_email_token_round_trip():
    token = tokens.make_email_token(42)
    assert tokens.verify_email_token(token) == 42


def test_unsubscribe_token_round_trip():
    token = tokens.make_unsubscribe_token(7)
    assert tokens.verify_unsubscribe_token(token) == 7


def test_tampered_email_token_rejected():
    token = tokens.make_email_token(42)
    tampered = token[:-2] + ("AA" if not token.endswith("AA") else "BB")
    with pytest.raises(HTTPException) as exc:
        tokens.verify_email_token(tampered)
    assert exc.value.status_code == 400


def test_wrong_salt_rejected():
    # An unsubscribe token must NOT validate as an email-action token (different salt).
    unsub = tokens.make_unsubscribe_token(42)
    with pytest.raises(HTTPException) as exc:
        tokens.verify_email_token(unsub)
    assert exc.value.status_code == 400


def test_expired_email_token_rejected(monkeypatch):
    # Force the max-age negative so any freshly minted token reads as expired.
    monkeypatch.setattr(get_settings(), "email_link_max_age_days", -1)
    token = tokens.make_email_token(42)
    with pytest.raises(HTTPException) as exc:
        tokens.verify_email_token(token)
    assert exc.value.status_code == 400
    assert "expired" in exc.value.detail.lower()
