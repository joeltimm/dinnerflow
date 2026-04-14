"""
Auth utilities:
- Password hashing / verification (bcrypt)
- Session token creation, validation, cleanup
- Fernet encryption/decryption for Todoist API tokens
"""
import secrets
import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from cryptography.fernet import Fernet

from config import get_settings

logger = logging.getLogger(__name__)


# ── Passwords ─────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ── Session tokens ─────────────────────────────────────────────────────────────

def _fernet() -> Fernet:
    key = get_settings().fernet_key
    return Fernet(key.encode() if isinstance(key, str) else key)


def create_session_token(conn, user_id: int) -> tuple[str, datetime]:
    """
    Generate a 32-byte URL-safe token, store it in user_sessions,
    and return (token, expires_at).
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=get_settings().session_duration_days)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO user_sessions (token, user_id, expires_at)
            VALUES (%s, %s, %s)
            """,
            (token, user_id, expires_at),
        )

    return token, expires_at


def cleanup_expired_sessions(conn) -> None:
    """Purge all expired sessions — call before every auth attempt."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM user_sessions WHERE expires_at <= NOW()")


# ── Fernet encryption for Todoist tokens ──────────────────────────────────────

def encrypt_token(plain: str) -> str:
    """Encrypt a plaintext API token before storing in DB."""
    return _fernet().encrypt(plain.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    """Decrypt an API token retrieved from DB."""
    return _fernet().decrypt(encrypted.encode()).decode()
