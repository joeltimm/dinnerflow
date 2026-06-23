"""
Gunicorn configuration — Prometheus multiprocess wiring.

With multiple worker processes, prometheus_client must run in *multiprocess*
mode: each worker writes counter/histogram samples to files under
``PROMETHEUS_MULTIPROC_DIR``, and the ``/metrics`` endpoint aggregates them via a
MultiProcessCollector (see services/metrics.py:latest).

This config:
  * clears stale sample files on master startup (otherwise dead workers' files
    accumulate across restarts and inflate counters),
  * marks a worker's files for cleanup when it exits.

Worker count comes from the CMD (--workers) / WEB_CONCURRENCY.
"""
import os

from prometheus_client import multiprocess

# Mirror the bind/timeout the image already used so behaviour is unchanged.
bind = "0.0.0.0:8000"
worker_class = "uvicorn.workers.UvicornWorker"
workers = int(os.environ.get("WEB_CONCURRENCY", "4"))
timeout = 1200
graceful_timeout = 30


def on_starting(server):
    """Wipe leftover multiprocess sample files before any worker starts."""
    mp_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if not mp_dir:
        return
    os.makedirs(mp_dir, exist_ok=True)
    for name in os.listdir(mp_dir):
        if name.endswith(".db"):
            try:
                os.remove(os.path.join(mp_dir, name))
            except OSError:
                pass


def child_exit(server, worker):
    """Drop a worker's gauge/counter files when it dies so totals stay correct."""
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        multiprocess.mark_process_dead(worker.pid)
