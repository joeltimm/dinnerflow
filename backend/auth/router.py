"""
Auth endpoints:
  POST /api/auth/register   — create account + send welcome email
  POST /api/auth/login      — validate credentials, set session cookie
  POST /api/auth/logout     — delete session, clear cookie
  GET  /api/auth/me         — return current user info
"""
import logging
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr

from config import get_settings
from database import get_db
from dependencies import get_current_user, invalidate_session
from limiter import limiter
from tasks import send_welcome_email as send_welcome_email_task
from auth.utils import (
    verify_password,
    hash_password,
    create_session_token,
    cleanup_expired_sessions,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

COOKIE_NAME = "session_token"


# ── Request/response models ───────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = True  # always create a session token


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    email_consent: bool = False


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str | None
    is_admin: bool
    dietary_preferences: str | None
    email_consent: bool


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest, response: Response, conn=Depends(get_db), settings=Depends(get_settings)):
    cleanup_expired_sessions(conn)

    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, email, full_name, password_hash, is_admin, dietary_preferences, email_consent "
            "FROM users WHERE email = %s",
            (body.email.lower(),),
        )
        user = cur.fetchone()

    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token, expires_at = create_session_token(conn, user["id"])

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.app_base_url.startswith("https://"),
        max_age=settings.session_duration_days * 86400,
        expires=expires_at.replace(tzinfo=None).isoformat(),
    )

    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "is_admin": user["is_admin"],
        "dietary_preferences": user["dietary_preferences"],
        "email_consent": user["email_consent"],
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, body: RegisterRequest, response: Response, conn=Depends(get_db), settings=Depends(get_settings)):
    # Check for existing account
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE email = %s", (body.email.lower(),))
        if cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )

    pw_hash = hash_password(body.password)

    consent_date = None
    if body.email_consent:
        from datetime import datetime, timezone
        consent_date = datetime.now(timezone.utc)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (email, password_hash, full_name, email_consent, email_consent_date)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, email, full_name, is_admin, dietary_preferences, email_consent
            """,
            (body.email.lower(), pw_hash, body.full_name, body.email_consent, consent_date),
        )
        new_user = cur.fetchone()

    token, expires_at = create_session_token(conn, new_user["id"])

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.app_base_url.startswith("https://"),
        max_age=settings.session_duration_days * 86400,
        expires=expires_at.replace(tzinfo=None).isoformat(),
    )

    # Send welcome email via Celery (non-blocking — runs in a background worker)
    try:
        send_welcome_email_task.delay(
            to_email=new_user["email"],
            user_name=new_user["full_name"] or "Chef",
        )
    except Exception as exc:
        logger.warning("Failed to enqueue welcome email (non-fatal): %s", exc)

    return {
        "id": new_user["id"],
        "email": new_user["email"],
        "full_name": new_user["full_name"],
        "is_admin": new_user["is_admin"],
        "dietary_preferences": new_user["dietary_preferences"],
        "email_consent": new_user["email_consent"],
    }


@router.post("/logout")
def logout(
    response: Response,
    conn=Depends(get_db),
    user=Depends(get_current_user),
    session_token: Optional[str] = Cookie(default=None),
):
    # Delete the session from DB so the token is immediately invalidated
    if session_token:
        invalidate_session(session_token)
        with conn.cursor() as cur:
            cur.execute("DELETE FROM user_sessions WHERE token = %s", (session_token,))
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/me")
def me(user=Depends(get_current_user)) -> dict:
    return user
