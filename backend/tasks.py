"""
Celery tasks — background work that should not block HTTP request handlers.

Tasks:
  send_welcome_email      — fire-and-forget welcome email on registration
  send_meal_plan_for_user — build + send a meal plan email for one user
  send_all_meal_plans     — fan-out: enqueue one send_meal_plan_for_user per user
  cleanup_sessions        — purge expired user_sessions rows
"""
import logging

import psycopg2.extras

from celery_app import app
from database import get_connection, init_pool

logger = logging.getLogger(__name__)


def _ensure_pool():
    """Celery workers run in separate processes — make sure the DB pool exists."""
    import database
    if database._pool is None:
        init_pool()


# ── Email tasks ──────────────────────────────────────────────────────────────

@app.task(name="tasks.send_welcome_email", ignore_result=True, max_retries=2)
def send_welcome_email(to_email: str, user_name: str):
    """Send onboarding email (called from registration endpoint)."""
    from services.email import send_welcome_email as _send
    try:
        _send(to_email=to_email, user_name=user_name)
    except Exception as exc:
        logger.error("Welcome email failed for %s: %s", to_email, exc)
        raise send_welcome_email.retry(exc=exc, countdown=30)


@app.task(name="tasks.send_meal_plan_for_user", ignore_result=True, max_retries=1)
def send_meal_plan_for_user(user_id: int, email: str, name: str):
    """Build and send a meal plan email for a single user (fan-out target)."""
    _ensure_pool()
    from services.scheduler import send_meal_plan_for_user as _send
    try:
        _send(user_id, email, name)
    except Exception as exc:
        logger.error("Meal plan task failed for user %d (%s): %s", user_id, email, exc)
        raise send_meal_plan_for_user.retry(exc=exc, countdown=60)


# ── Scheduled tasks ──────────────────────────────────────────────────────────

@app.task(name="tasks.send_all_meal_plans", ignore_result=True)
def send_all_meal_plans():
    """
    Scheduled job (Tue/Sat 10:30 AM): fan out meal plan emails to all users.

    Instead of processing users sequentially (which takes hours at scale),
    this enqueues one send_meal_plan_for_user task per user. Celery workers
    process them in parallel.
    """
    _ensure_pool()
    logger.info("Scheduled meal plan run — fanning out to workers...")

    with get_connection() as conn:
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        with conn.cursor() as cur:
            cur.execute("SELECT id, email, full_name FROM users")
            users = [dict(r) for r in cur.fetchall()]

    logger.info("Enqueuing meal plan tasks for %d users", len(users))
    for u in users:
        send_meal_plan_for_user.delay(u["id"], u["email"], u.get("full_name", "Chef"))


@app.task(name="tasks.cleanup_sessions", ignore_result=True)
def cleanup_sessions():
    """Purge expired user_sessions rows (daily 3 AM)."""
    _ensure_pool()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM user_sessions WHERE expires_at <= NOW()")
            deleted = cur.rowcount
    logger.info("Expired sessions cleaned up (%d deleted).", deleted)
