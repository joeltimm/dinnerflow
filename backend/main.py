"""
Iron Skillet — FastAPI application entry point.

Mounts all routers, serves uploaded images as static files,
and manages the scheduler lifecycle.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from limiter import limiter

from config import get_settings
from database import close_pool, init_pool

# Routers
from auth.router import router as auth_router
from routers.recipes import router as recipes_router
from routers.chef import router as chef_router
from routers.settings import router as settings_router
from routers.dashboard import router as dashboard_router
from routers.admin import router as admin_router
from routers.tonight import router as tonight_router
from routers.shopping import router as shopping_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup → yield → shutdown."""
    settings = get_settings()

    # Ensure uploads directory exists
    Path(settings.uploads_path).mkdir(parents=True, exist_ok=True)

    # Initialise DB pool
    init_pool()
    logger.info("App starting — DB pool ready.")

    # Warn early if Gmail token is missing — email will fail at send time but app still runs
    from pathlib import Path as _Path
    sender = settings.sender_email
    if sender:
        suffix = sender.split("@")[0]
        token_path = _Path(settings.google_auth_path) / f"token_{suffix}.json"
        if not token_path.exists():
            logger.warning(
                "Gmail token not found at %s — email sending will fail. "
                "Run backend/scripts/generate_gmail_token.py to fix.",
                token_path,
            )
    else:
        logger.warning("SENDER_EMAIL is not set — email sending is disabled.")

    yield  # ── application is running ──

    close_pool()
    logger.info("App shutdown complete.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Iron Skillet API",
        description="Self-hosted AI-powered meal planning backend",
        version="2.0.0",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # CORS — allow the React frontend origin(s)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,   # Required for cookie-based sessions
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # API routers
    app.include_router(auth_router)
    app.include_router(recipes_router)
    app.include_router(chef_router)
    app.include_router(settings_router)
    app.include_router(dashboard_router)
    app.include_router(admin_router)
    app.include_router(tonight_router)
    app.include_router(shopping_router)

    # Serve uploaded recipe images at /uploads/<filename>
    uploads_path = Path(settings.uploads_path)
    uploads_path.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
