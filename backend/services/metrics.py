"""
Application metrics — Prometheus instrumentation with a back-compatible shim.

Two layers live here:

1. **Legacy in-process counters** (``inc`` / ``snapshot``). These still back the
   ``/health`` endpoint so a quick per-worker sample is available without a
   metrics backend. Counters are per-process (each gunicorn/celery worker has
   its own), so treat the /health numbers as a sample, not a global total.

2. **Prometheus metrics** (the ``Counter`` / ``Histogram`` objects below plus the
   ``record_*`` helpers). These are scraped at ``/metrics`` and aggregated across
   workers by Prometheus. When ``PROMETHEUS_MULTIPROC_DIR`` is set (it is in the
   Docker images), prometheus_client transparently writes counter/histogram
   samples to that directory so the 4 gunicorn workers / 8 celery prefork
   children aggregate correctly; ``latest()`` builds a MultiProcessCollector
   registry at scrape time.

Call sites should prefer the ``record_*`` helpers — they update both layers so
``/health`` and ``/metrics`` stay consistent.
"""
import os
import threading
from collections import defaultdict

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
    multiprocess,
)

# ── Legacy per-process counters (still surfaced on /health) ────────────────────
_lock = threading.Lock()
_counters: dict[str, int] = defaultdict(int)


def inc(name: str, n: int = 1) -> None:
    """Increment a legacy in-process counter (per-worker; surfaced on /health)."""
    with _lock:
        _counters[name] += n


def snapshot() -> dict[str, int]:
    """Return a copy of this worker's legacy counters (for /health)."""
    with _lock:
        return dict(_counters)


# ── Prometheus metrics ─────────────────────────────────────────────────────────
# Naming: <subsystem>_<thing>_total for counters, _seconds for histograms.

# HTTP (RED method) — populated by the middleware in main.py.
HTTP_REQUESTS = Counter(
    "ironskillet_http_requests_total",
    "HTTP requests handled by the API.",
    ["method", "route", "status"],
)
HTTP_REQUEST_DURATION = Histogram(
    "ironskillet_http_request_duration_seconds",
    "HTTP request latency, by route.",
    ["method", "route"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60),
)

# LLM / embeddings — the AI heart of the app.
LLM_CALLS = Counter(
    "ironskillet_llm_calls_total",
    "LLM / embedding calls to the local OpenAI-compatible endpoint.",
    ["operation", "outcome"],  # operation: chat|embedding  outcome: ok|failed
)
LLM_RETRIES = Counter(
    "ironskillet_llm_retries_total",
    "Transient LLM/embedding call retries (connection/timeout).",
    ["operation"],
)
LLM_DURATION = Histogram(
    "ironskillet_llm_request_duration_seconds",
    "LLM / embedding call latency (the local model is slow — wide buckets).",
    ["operation"],
    buckets=(0.1, 0.5, 1, 2.5, 5, 10, 20, 30, 60, 120, 300, 600, 1200),
)

# Scraping (recipe import from URLs).
SCRAPES = Counter(
    "ironskillet_scrapes_total",
    "Recipe page fetch + clean attempts.",
    ["outcome"],  # ok|failed
)

# Email (welcome + weekly meal plans).
EMAILS = Counter(
    "ironskillet_emails_total",
    "Outbound emails by type and outcome.",
    ["type", "outcome"],  # type: welcome|meal_plan  outcome: ok|failed
)
EMAIL_LINK_CLICKS = Counter(
    "ironskillet_email_link_clicks_total",
    'Clicks on "Add to My Recipes" links in meal-plan emails.',
)

# Business events.
RECIPES_IMPORTED = Counter(
    "ironskillet_recipes_imported_total",
    "Recipes added, by entry method.",
    ["method"],  # manual|url|email_select|instant_chef|...
)
MEALS_COOKED = Counter(
    "ironskillet_meals_cooked_total",
    "Cook sessions logged.",
)
RECIPE_RATINGS = Histogram(
    "ironskillet_recipe_rating_stars",
    "Star ratings submitted (1-5).",
    buckets=(1, 2, 3, 4, 5),
)
DUPLICATE_DETECTIONS = Counter(
    "ironskillet_duplicate_detections_total",
    "pgvector duplicate checks on import, by result.",
    ["result"],  # duplicate|unique
)
TODOIST_SYNCS = Counter(
    "ironskillet_todoist_syncs_total",
    "Todoist ingredient syncs, by outcome.",
    ["outcome"],  # ok|failed
)
SHOPPING_ITEMS_ADDED = Counter(
    "ironskillet_shopping_items_added_total",
    "Shopping-list items added, by source.",
    ["source"],  # manual|recipe
)


# ── record_* helpers — update both Prometheus and the legacy /health counters ──
def record_llm(operation: str, outcome: str, duration: float | None = None) -> None:
    LLM_CALLS.labels(operation=operation, outcome=outcome).inc()
    if duration is not None:
        LLM_DURATION.labels(operation=operation).observe(duration)
    # Legacy names kept stable for /health back-compat.
    if operation == "chat":
        inc("llm_calls_ok" if outcome == "ok" else "llm_calls_failed")


def record_llm_retry(operation: str) -> None:
    LLM_RETRIES.labels(operation=operation).inc()


def record_scrape(outcome: str) -> None:
    SCRAPES.labels(outcome=outcome).inc()
    inc("scrapes_ok" if outcome == "ok" else "scrapes_failed")


def record_email(email_type: str, outcome: str = "ok") -> None:
    EMAILS.labels(type=email_type, outcome=outcome).inc()
    if outcome == "ok":
        inc("emails_sent")


def record_email_link_click() -> None:
    EMAIL_LINK_CLICKS.inc()
    inc("email_link_clicks")


def record_recipe_import(method: str) -> None:
    RECIPES_IMPORTED.labels(method=method or "unknown").inc()
    inc("recipes_imported")


def record_cook() -> None:
    MEALS_COOKED.inc()
    inc("meals_cooked")


def record_rating(stars: int) -> None:
    try:
        RECIPE_RATINGS.observe(float(stars))
    except (TypeError, ValueError):
        return


def record_duplicate(is_duplicate: bool) -> None:
    DUPLICATE_DETECTIONS.labels(result="duplicate" if is_duplicate else "unique").inc()


def record_todoist_sync(outcome: str) -> None:
    TODOIST_SYNCS.labels(outcome=outcome).inc()


def record_shopping_add(source: str, n: int = 1) -> None:
    SHOPPING_ITEMS_ADDED.labels(source=source).inc(n)


# ── Exposition ─────────────────────────────────────────────────────────────────
def latest() -> tuple[bytes, str]:
    """
    Render the current metrics for a ``/metrics`` scrape.

    In multiprocess mode (``PROMETHEUS_MULTIPROC_DIR`` set) we build a fresh
    registry backed by a MultiProcessCollector so all worker processes are
    aggregated. Otherwise we fall back to the default global registry.
    """
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        return generate_latest(registry), CONTENT_TYPE_LATEST
    return generate_latest(), CONTENT_TYPE_LATEST
