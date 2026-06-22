"""
Tiny in-process metrics counters surfaced on /health.

Not a replacement for a real metrics backend — just enough to spot silent
failures (LLM errors, scrape failures, email problems) without trawling logs.
Counters are per-process (each gunicorn/celery worker has its own), so treat the
/health numbers as a sample from one backend worker, not a global total.
"""
import threading
from collections import defaultdict

_lock = threading.Lock()
_counters: dict[str, int] = defaultdict(int)


def inc(name: str, n: int = 1) -> None:
    with _lock:
        _counters[name] += n


def snapshot() -> dict[str, int]:
    with _lock:
        return dict(_counters)
