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
    dinner_db_port: int = 5436

    # ── Security ──────────────────────────────────────────────────────────────
    # Fernet key for encrypting Todoist API tokens stored in DB
    fernet_key: str
    # Secret key for signing email action links (itsdangerous)
    secret_key: str

    # ── LLM (OpenAI-compatible local endpoint) ────────────────────────────────
    llm_base_url: str = "http://100.98.99.49:8081/v1"
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
