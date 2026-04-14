"""
Database connection pool using psycopg2.ThreadedConnectionPool.

Usage in FastAPI routes (via dependency injection):
    def my_route(conn=Depends(get_db)):
        with conn.cursor() as cur:
            cur.execute("SELECT ...")
"""
import logging
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool

from config import get_settings

logger = logging.getLogger(__name__)

# Module-level pool — initialized on app startup, closed on shutdown
_pool: ThreadedConnectionPool | None = None


def init_pool() -> None:
    """Create the connection pool. Called once at app startup."""
    global _pool
    settings = get_settings()
    _pool = ThreadedConnectionPool(
        minconn=settings.db_pool_min,
        maxconn=settings.db_pool_max,
        dsn=settings.db_dsn,
    )
    logger.info("Database connection pool initialized.")


def close_pool() -> None:
    """Drain and close the pool. Called on app shutdown."""
    global _pool
    if _pool:
        _pool.closeall()
        logger.info("Database connection pool closed.")


@contextmanager
def get_connection():
    """Context manager that checks out a connection and returns it to the pool."""
    if _pool is None:
        raise RuntimeError("Database pool is not initialized. Call init_pool() first.")
    conn = _pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


def get_db():
    """
    FastAPI dependency that yields a psycopg2 connection with RealDictCursor.
    Rows returned as dicts (column name → value) instead of tuples.
    """
    with get_connection() as conn:
        # Switch to dict cursor so rows behave like dicts
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        yield conn
