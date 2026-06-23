# Iron Skillet — Monitoring

Prometheus + Grafana observability for the stack. Custom application metrics are
emitted by the app (`backend/services/metrics.py`); the rest comes from
off-the-shelf exporters wired into `compose.yml`.

## What's exposed

| Source | Port (127.0.0.1) | Metrics |
|---|---|---|
| Backend `/metrics` | `8010` | HTTP RED (`ironskillet_http_*`), LLM (`ironskillet_llm_*`), business events |
| Celery worker `/metrics` | `9111` | In-task counters (embeds, scrapes, emails, email-link imports, Todoist) |
| celery-exporter | `9808` | Task sent/started/succeeded/failed/runtime, worker up, queue length |
| postgres-exporter | `9187` | PG internals **+** `ironskillet_*` business gauges ([postgres_queries.yaml](postgres_queries.yaml)) |
| redis-exporter | `9121` | Redis memory/ops + Celery queue backlog |
| node-exporter | `9100` | Host CPU / memory / disk / network |
| cAdvisor | `9101` | Per-container CPU / memory / network |

All exporter ports bind to `127.0.0.1` — Prometheus is expected to run on the
same host. (Note `8010` is the backend's existing debug port; nginx still serves
users on `:80` and never exposes `/metrics`.)

## Setup

1. **Bring up the exporters** (the app/worker changes ship in the backend image):

   ```bash
   docker compose up -d --build
   ```

2. **Point your Prometheus** at the new targets — paste the jobs from
   [`prometheus-scrape.yml`](prometheus-scrape.yml) into your
   `scrape_configs:` and reload Prometheus.

3. **Verify** targets are UP at `http://<host>:9090/targets`, then spot-check:

   ```bash
   curl -s 127.0.0.1:8010/metrics | grep ironskillet_ | head
   curl -s 127.0.0.1:9111/metrics | grep ironskillet_ | head
   curl -s 127.0.0.1:9187/metrics | grep ironskillet_ | head
   ```

4. **Import the dashboard**: Grafana → Dashboards → Import →
   upload [`grafana-dashboard.json`](grafana-dashboard.json) and pick your
   Prometheus datasource. It has 6 rows / ~37 panels: Overview, HTTP (RED),
   LLM/AI, Celery, Business, Infrastructure.

## Architecture notes

- **Multiprocess aggregation.** Gunicorn runs 4 workers and Celery runs 8
  prefork children. `prometheus_client` runs in multiprocess mode
  (`PROMETHEUS_MULTIPROC_DIR`, set in the Dockerfile); each process writes
  samples to a shared dir and `/metrics` aggregates them. `gunicorn_conf.py`
  cleans up dead workers' files; the worker's server is started from
  `celery_app.py`'s `worker_init` signal.
- **Counters vs. gauges.** Event rates (requests, LLM calls, imports, cooks) are
  Prometheus counters in the app. Stateful totals (recipe/user counts, ratings
  distribution, embedding coverage, table sizes) come from postgres-exporter SQL
  so they're exact and global, not per-worker.
- **`/health` unchanged.** The legacy per-worker counters still back `/health`;
  the `record_*` helpers update both it and Prometheus.

## Community dashboards worth adding alongside

These pair well with the exporters above (import by ID in Grafana):

- **1860** — Node Exporter Full (host)
- **893 / 14282** — Docker / cAdvisor
- **9628** — PostgreSQL (postgres-exporter)
- **763 / 11835** — Redis (redis-exporter)
- celery-exporter ships its own dashboard in its repo
