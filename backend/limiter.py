import os

from slowapi import Limiter
from slowapi.util import get_remote_address

# Use Redis as the limiter store so rate limits are enforced GLOBALLY across the
# gunicorn worker processes (4 by default). With the default in-memory storage
# each worker keeps its own counter, making every limit ~Nx looser than written.
# Falls back to in-memory if REDIS_URL is unset (e.g. local non-Docker dev).
_redis_url = os.environ.get("REDIS_URL")

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_redis_url or "memory://",
)
