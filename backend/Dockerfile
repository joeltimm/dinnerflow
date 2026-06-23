FROM python:3.11-slim

WORKDIR /app

# Install system deps for psycopg2 and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create uploads directory (also mounted as a volume in compose)
RUN mkdir -p /app/uploads

# Prometheus multiprocess sample dir — the 4 gunicorn workers (and celery prefork
# children) write counter/histogram samples here so /metrics aggregates correctly.
# See gunicorn_conf.py and services/metrics.py.
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
RUN mkdir -p /tmp/prometheus_multiproc

EXPOSE 8000

# WEB_CONCURRENCY controls worker count (default 4).
# Each worker is a separate process with its own thread pool.
# Bind/timeout + multiprocess cleanup hooks live in gunicorn_conf.py.
CMD ["gunicorn", "main:app", \
     "-c", "gunicorn_conf.py", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "1200", \
     "--graceful-timeout", "30"]
