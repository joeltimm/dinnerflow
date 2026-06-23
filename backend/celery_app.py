"""
Celery application — broker and beat schedule.

Replaces APScheduler with a distributed task queue that works correctly
across multiple backend workers/containers.

Usage:
  Worker:  celery -A celery_app worker --loglevel=info --concurrency=8
  Beat:    celery -A celery_app beat --loglevel=info
"""
import logging
import os

from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_init

from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Port the worker exposes its custom app metrics on (LLM/embed/scrape/email/import
# counters incremented inside tasks). Prometheus scrapes celery-worker:9111.
WORKER_METRICS_PORT = int(os.environ.get("CELERY_METRICS_PORT", "9111"))

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
    # Emit task-lifecycle events so the off-the-shelf celery-exporter can report
    # per-task sent/started/succeeded/failed/runtime and queue length.
    worker_send_task_events=True,
    task_send_sent_event=True,
)


@worker_init.connect
def _start_worker_metrics_server(**_kwargs):
    """
    Expose the worker's custom Prometheus metrics on WORKER_METRICS_PORT.

    Task-level metrics (success/failure/runtime/queue depth) come from the
    separate celery-exporter container via task events. This server surfaces the
    *in-task* business counters (LLM calls, embeddings, scrapes, emails, recipe
    imports from email links, Todoist syncs) that the app records via
    services.metrics. Prefork children write samples to PROMETHEUS_MULTIPROC_DIR;
    this server (in the worker's main process) aggregates them at scrape time.
    """
    from prometheus_client import (
        CollectorRegistry,
        multiprocess,
        start_http_server,
    )

    mp_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if mp_dir:
        # Clear stale samples from a previous run so counters don't double-count.
        os.makedirs(mp_dir, exist_ok=True)
        for name in os.listdir(mp_dir):
            if name.endswith(".db"):
                try:
                    os.remove(os.path.join(mp_dir, name))
                except OSError:
                    pass
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
    else:
        registry = None  # default global registry

    try:
        start_http_server(WORKER_METRICS_PORT, registry=registry)
        logger.info("Celery worker metrics server on :%d/metrics", WORKER_METRICS_PORT)
    except OSError as exc:
        # Beat or a second worker on the same host may bind first — non-fatal.
        logger.warning("Could not start worker metrics server: %s", exc)

# Beat schedule — replaces APScheduler jobs
app.conf.beat_schedule = {
    # Fire every minute; send_all_meal_plans checks each consented user's local
    # clock (users.timezone_name + meal_plan_hour/minute) and chosen email_days,
    # and uses last_meal_plan_sent_at to send at most once per local day.
    "meal-plans-tick": {
        "task": "tasks.send_all_meal_plans",
        "schedule": crontab(minute="*"),
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
