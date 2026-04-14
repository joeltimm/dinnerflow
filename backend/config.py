"""
Application configuration loaded from environment variables.
All secrets should be set in .env (not committed) or passed via Docker environment.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────────
    dinner_db_name: str = "dinnerflow"
    dinner_db_user: str = "dinneruser"
    dinner_db_password: str
    dinner_db_host: str = "dinner-db"
    # Internal container port (5432). Host-side mapping is 5436 — see compose.yml.
    dinner_db_port: int = 5432

    # ── Security ──────────────────────────────────────────────────────────────
    # Fernet key for encrypting Todoist API tokens stored in DB
    fernet_key: str
    # Secret key for signing email action links (itsdangerous)
    secret_key: str

    # ── LLM (OpenAI-compatible local endpoint) ────────────────────────────────
    # Must be set in .env or compose.yml (e.g. http://host:8081/v1)
    llm_base_url: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_timeout: int = 1200  # seconds — local model is slow; recipe extraction can take 15+ min

    # ── Tavily (web search for recipe ideas) ──────────────────────────────────
    tavily_api_key: str = ""

    # ── Gmail OAuth (mirrors calendar_bot pattern) ────────────────────────────
    # Path to directory containing token_{suffix}.json files
    google_auth_path: str = "/app/google_auth"
    # Full email address used to send mail (e.g. joeltimm@gmail.com)
    sender_email: str = ""

    # ── Database pool ────────────────────────────────────────────────────────
    db_pool_min: int = 2
    db_pool_max: int = 50

    # ── Redis (Celery broker + result backend) ────────────────────────────────
    redis_url: str = "redis://redis:6379/0"

    # ── App ───────────────────────────────────────────────────────────────────
    # Public base URL — used to build links in emails
    app_base_url: str = "http://localhost:8000"
    # Path where uploaded recipe images are stored
    uploads_path: str = "/app/uploads"

    # ── CORS / Frontend ───────────────────────────────────────────────────────
    # Origin(s) allowed for CORS (space-separated if multiple)
    cors_origins: str = "http://localhost:5173"

    # ── Sessions & tokens ────────────────────────────────────────────────────
    session_duration_days: int = 30
    email_link_max_age_days: int = 7
    unsubscribe_link_max_age_days: int = 90

    # ── Data retention ───────────────────────────────────────────────────────
    data_retention_days: int = 90

    # ── Image uploads ────────────────────────────────────────────────────────
    max_image_size_bytes: int = 10_485_760  # 10 MB
    image_resize_px: int = 800
    image_quality: int = 85

    # ── Monitoring thresholds ────────────────────────────────────────────────
    disk_warn_pct: int = 80
    disk_crit_pct: int = 90

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Allows reading from a nested .env in parent dirs
        extra = "ignore"

    @property
    def db_dsn(self) -> str:
        """PostgreSQL DSN string for psycopg2."""
        return (
            f"postgresql://{self.dinner_db_user}:{self.dinner_db_password}"
            f"@{self.dinner_db_host}:{self.dinner_db_port}/{self.dinner_db_name}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split() if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — call this everywhere instead of constructing Settings()."""
    return Settings()
