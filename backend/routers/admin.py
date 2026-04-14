"""
Admin-only endpoints.

GET  /api/admin/users           — list all users
GET  /api/admin/users/{id}      — get a user's full profile
POST /api/admin/impersonate/{id} — create a session token for another user
                                   (returns a token the admin can use to view as that user)
"""
from fastapi import APIRouter, Depends, HTTPException

from auth.utils import create_session_token
from database import get_db
from dependencies import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users")
def list_users(conn=Depends(get_db), _=Depends(require_admin)):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, email, full_name, is_admin, created_at, dietary_preferences "
            "FROM users ORDER BY created_at DESC"
        )
        return [dict(r) for r in cur.fetchall()]


@router.get("/users/{user_id}")
def get_user(user_id: int, conn=Depends(get_db), _=Depends(require_admin)):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, email, full_name, is_admin, created_at, dietary_preferences "
            "FROM users WHERE id = %s",
            (user_id,),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)


@router.post("/impersonate/{user_id}")
def impersonate(user_id: int, conn=Depends(get_db), admin=Depends(require_admin)):
    """
    Creates a temporary session token for another user.
    The admin can use this token (e.g. in the cookie) to view the app as that user.
    Replicates the Streamlit admin impersonation feature.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT id, email FROM users WHERE id = %s", (user_id,))
        target = cur.fetchone()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    token, expires_at = create_session_token(conn, user_id)
    return {
        "token": token,
        "expires_at": expires_at.isoformat(),
        "user_id": user_id,
        "email": target["email"],
        "note": "Set this as the session_token cookie to view the app as this user.",
    }
