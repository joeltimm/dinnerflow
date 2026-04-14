"""
Shared FastAPI dependencies.

- get_db: yields a DB connection (delegates to database.py)
- get_current_user: reads session cookie, validates against user_sessions table
- require_admin: like get_current_user but also asserts is_admin == true
"""
import threading

from cachetools import TTLCache
from fastapi import Cookie, Depends, HTTPException, status
from typing import Optional

from database import get_db

# In-memory session cache — avoids a DB round-trip on every authenticated request.
# TTL of 60s means a revoked session stays valid for at most 1 minute.
_session_cache: TTLCache = TTLCache(maxsize=4096, ttl=60)
_cache_lock = threading.Lock()


def invalidate_session(token: str) -> None:
    """Remove a session from the cache (called on logout)."""
    with _cache_lock:
        _session_cache.pop(token, None)


def get_current_user(
    session_token: Optional[str] = Cookie(default=None),
    conn=Depends(get_db),
) -> dict:
    """
    Validate the session_token cookie and return the user row.
    Raises 401 if missing, expired, or invalid.
    """
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Check cache first
    with _cache_lock:
        cached = _session_cache.get(session_token)
    if cached is not None:
        return cached

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.id, u.email, u.full_name, u.is_admin, u.dietary_preferences, u.email_consent
            FROM user_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = %s
              AND s.expires_at > NOW()
            """,
            (session_token,),
        )
        user = cur.fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
        )

    result = dict(user)
    with _cache_lock:
        _session_cache[session_token] = result
    return result


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Like get_current_user, but also requires is_admin = true."""
    if not user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
