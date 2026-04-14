"""
User settings endpoints.

GET  /api/settings/preferences         — get dietary preferences
PUT  /api/settings/preferences         — update dietary preferences
GET  /api/settings/todoist             — get Todoist integration status
POST /api/settings/todoist             — save + verify Todoist token
DELETE /api/settings/todoist           — disconnect Todoist
GET  /api/settings/todoist/projects    — list user's Todoist projects
PUT  /api/settings/todoist/project     — set the active grocery list project
POST /api/settings/todoist/project     — create a new project and set it active
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from auth.utils import decrypt_token, encrypt_token
from database import get_db
from dependencies import get_current_user
from services import todoist as todoist_svc

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/settings", tags=["settings"])


# ── Request models ────────────────────────────────────────────────────────────

class PreferencesUpdate(BaseModel):
    dietary_preferences: str


class TodoistSave(BaseModel):
    api_token: str


class ProjectSelect(BaseModel):
    project_id: str
    project_name: str


class ProjectCreate(BaseModel):
    name: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_todoist_token_row(conn, user_id: int) -> dict | None:
    """Return the raw user_integrations row for the user's Todoist, or None."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT api_token FROM user_integrations "
            "WHERE user_id = %s AND provider = 'todoist'",
            (user_id,),
        )
        return cur.fetchone()


# ── Preferences ───────────────────────────────────────────────────────────────

@router.get("/preferences")
def get_preferences(conn=Depends(get_db), user=Depends(get_current_user)):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT dietary_preferences FROM users WHERE id = %s", (user["id"],)
        )
        return cur.fetchone()


@router.put("/preferences")
def update_preferences(
    body: PreferencesUpdate,
    conn=Depends(get_db),
    user=Depends(get_current_user),
):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET dietary_preferences = %s WHERE id = %s",
            (body.dietary_preferences, user["id"]),
        )
    return {"ok": True}


# ── Todoist ───────────────────────────────────────────────────────────────────

@router.get("/todoist")
def get_todoist(conn=Depends(get_db), user=Depends(get_current_user)):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT target_list_id, target_list_name FROM user_integrations "
            "WHERE user_id = %s AND provider = 'todoist'",
            (user["id"],),
        )
        row = cur.fetchone()

    if not row:
        return {"connected": False}

    return {
        "connected": True,
        "target_list_id": row["target_list_id"],
        "target_list_name": row["target_list_name"],
    }


@router.post("/todoist")
def save_todoist_token(
    body: TodoistSave,
    conn=Depends(get_db),
    user=Depends(get_current_user),
):
    """Validate the token against Todoist API, then encrypt and store it."""
    if not todoist_svc.verify_token(body.api_token):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid Todoist API token",
        )

    encrypted = encrypt_token(body.api_token)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO user_integrations (user_id, provider, api_token)
            VALUES (%s, 'todoist', %s)
            ON CONFLICT (user_id, provider) DO UPDATE SET api_token = EXCLUDED.api_token
            """,
            (user["id"], encrypted),
        )

    return {"ok": True}


@router.delete("/todoist", status_code=status.HTTP_204_NO_CONTENT)
def delete_todoist(conn=Depends(get_db), user=Depends(get_current_user)):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM user_integrations WHERE user_id = %s AND provider = 'todoist'",
            (user["id"],),
        )


@router.get("/todoist/projects")
def list_todoist_projects(conn=Depends(get_db), user=Depends(get_current_user)):
    row = _get_todoist_token_row(conn, user["id"])
    if not row:
        raise HTTPException(status_code=404, detail="Todoist not connected")

    try:
        token = decrypt_token(row["api_token"])
        projects = todoist_svc.get_projects(token)
        return projects
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Todoist error: {exc}")


@router.put("/todoist/project")
def select_project(
    body: ProjectSelect,
    conn=Depends(get_db),
    user=Depends(get_current_user),
):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE user_integrations
            SET target_list_id = %s, target_list_name = %s
            WHERE user_id = %s AND provider = 'todoist'
            """,
            (body.project_id, body.project_name, user["id"]),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Todoist not connected")
    return {"ok": True}


@router.post("/todoist/project")
def create_project(
    body: ProjectCreate,
    conn=Depends(get_db),
    user=Depends(get_current_user),
):
    row = _get_todoist_token_row(conn, user["id"])
    if not row:
        raise HTTPException(status_code=404, detail="Todoist not connected")

    token = decrypt_token(row["api_token"])
    new_id = todoist_svc.create_project(token, body.name)

    with conn.cursor() as cur:
        cur.execute(
            "UPDATE user_integrations SET target_list_id = %s, target_list_name = %s "
            "WHERE user_id = %s AND provider = 'todoist'",
            (new_id, body.name, user["id"]),
        )

    return {"project_id": new_id, "name": body.name}
