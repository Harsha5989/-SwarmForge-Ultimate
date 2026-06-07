"""SwarmForge Ultimate — Application Settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration loaded from environment variables."""

    # ── Database ───────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://swarm:swarmpass123@postgres:5432/swarmforge"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "swarmforge"
    postgres_user: str = "swarm"
    postgres_password: str = "swarmpass123"

    # ── Redis ──────────────────────────────────────────────────
    redis_url: str = "redis://redis:6379/0"

    # ── LiteLLM ────────────────────────────────────────────────
    litellm_base_url: str = "http://litellm:4000"
    litellm_api_key: str = "sk-swarmforge-local"

    # ── External API Keys ──────────────────────────────────────
    groq_api_key: str = ""
    openrouter_api_key: str = ""

    # ── Pipeline Tuning ────────────────────────────────────────
    max_iterations: int = 5
    build_gate_min_score: float = 80.0
    test_gate_min_coverage: float = 90.0
    security_gate_min_score: float = 85.0
    perf_gate_max_p95_ms: float = 200.0
    final_gate_min_score: float = 85.0
    max_retries_per_gate: int = 3

    # ── Sandbox ────────────────────────────────────────────────
    sandbox_container: str = "ultimate_worker-sandbox-1"
    sandbox_timeout_sec: int = 120
    output_dir: str = "/workspace/output"

    # ── Application ────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "changeme-in-production-use-random-32-chars"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
