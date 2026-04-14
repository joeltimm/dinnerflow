"""
Celery application — broker and beat schedule.

Replaces APScheduler with a distributed task queue that works correctly
across multiple backend workers/containers.

Usage:
  Worker:  celery -A celery_app worker --loglevel=info --concurrency=8
  Beat:    celery -A celery_app beat --loglevel=info
"""
from celery import Celery
from celery.schedules import crontab

from config import get_settings

settings = get_settings()

app = Celery(
    "ironskillet",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["tasks"],
)

app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Timezone
    timezone="America/Chicago",
    enable_utc=True,
    # Reliability
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Result expiry (1 hour)
    result_expires=3600,
)

# Beat schedule — replaces APScheduler jobs
app.conf.beat_schedule = {
    "meal-plans-tue-sat": {
        "task": "tasks.send_all_meal_plans",
        "schedule": crontab(hour=10, minute=30, day_of_week="tue,sat"),
    },
    "session-cleanup-daily": {
        "task": "tasks.cleanup_sessions",
        "schedule": crontab(hour=3, minute=0),
    },
    "disk-db-usage-check": {
        "task": "tasks.check_disk_and_db_usage",
        "schedule": crontab(hour=4, minute=0),
    },
    "data-retention-cleanup": {
        "task": "tasks.cleanup_stale_data",
        "schedule": crontab(hour=4, minute=30, day_of_week="sun"),
    },
}
