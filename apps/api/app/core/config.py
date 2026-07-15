"""Central configuration. All values come from the environment (never hardcoded).

Secrets (JWT, LLM key, DB/MinIO passwords) live only here and only in the services that
need them. Frontend and sanitizer never import this module.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")

    # Postgres — the app connects as the app role; Alembic connects as the migrator role.
    postgres_host: str = Field(default="postgres", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="sanad", alias="POSTGRES_DB")
    app_user: str = Field(default="sanad_app", alias="SANAD_APP_USER")
    app_password: str = Field(default="", alias="SANAD_APP_PASSWORD")
    migrator_user: str = Field(default="sanad_migrator", alias="SANAD_MIGRATOR_USER")
    migrator_password: str = Field(default="", alias="SANAD_MIGRATOR_PASSWORD")

    # Redis / arq
    redis_host: str = Field(default="redis", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")

    # MinIO
    minio_endpoint: str = Field(default="minio:9000", alias="MINIO_ENDPOINT")
    minio_public_endpoint: str = Field(default="localhost:9000", alias="MINIO_PUBLIC_ENDPOINT")
    minio_use_ssl: bool = Field(default=False, alias="MINIO_USE_SSL")
    # Whether the browser-facing (public) MinIO endpoint uses TLS. Presigned URLs are signed
    # for this endpoint so the Host header matches what the browser sends (SigV4).
    minio_public_secure: bool = Field(default=False, alias="MINIO_PUBLIC_SECURE")
    minio_root_user: str = Field(default="", alias="MINIO_ROOT_USER")
    minio_root_password: str = Field(default="", alias="MINIO_ROOT_PASSWORD")
    bucket_quarantine: str = Field(default="sanad-quarantine", alias="MINIO_BUCKET_QUARANTINE")
    bucket_sanitized: str = Field(default="sanad-sanitized", alias="MINIO_BUCKET_SANITIZED")

    # Embedder
    embedder_url: str = Field(default="http://embedder:8081", alias="EMBEDDER_URL")
    embedding_dim: int = Field(default=1024, alias="EMBEDDING_DIM")

    # Retrieval reranking (PLAN.md P1.6): fetch a wide cosine net, LLM-rerank to top-k.
    rerank_enabled: bool = Field(default=True, alias="RERANK_ENABLED")
    # Wide net: at 1600+ articles the on-point article often ranks 50-100 by cosine (other-law
    # collisions), so the net must be wide for recall; the reranker then restores precision.
    rerank_fetch_k: int = Field(default=100, alias="RERANK_FETCH_K")

    # Retrieval confidence tiers (spec #1). Signal is derived from cosine similarity of the
    # cited article (sim = 1 - cosine_distance) and its margin over the next-best candidate.
    # Anchor: _RELEVANCE_MAX_DISTANCE=0.42 (dist) => sim 0.58 is the irrelevance floor.
    # PROVISIONAL defaults — calibrate against the real reranker score distribution (raw
    # match_score/match_margin are stored on every finding for exactly this purpose).
    confidence_min_sim: float = Field(default=0.62, alias="CONFIDENCE_MIN_SIM")
    confidence_high_sim: float = Field(default=0.72, alias="CONFIDENCE_HIGH_SIM")
    confidence_min_margin: float = Field(default=0.04, alias="CONFIDENCE_MIN_MARGIN")

    # Retrieval sufficiency (spec #2): if the best candidate's cosine distance exceeds this,
    # nothing relevant was retrieved for the clause -> mark it retrieval_insufficient rather
    # than silently returning zero findings. Same anchor as the offline stub's relevance gate.
    retrieval_relevance_max_distance: float = Field(default=0.42, alias="RETRIEVAL_RELEVANCE_MAX_DISTANCE")

    # Corpus staleness (spec #7): a regulation not reconciled against its source within this
    # many days is flagged stale in the Admin corpus view.
    corpus_stale_days: int = Field(default=30, alias="CORPUS_STALE_DAYS")

    # LLM (behind services/llm only)
    llm_provider: str = Field(default="selfhosted", alias="LLM_PROVIDER")
    llm_model: str = Field(default="claude-sonnet-4-20250514", alias="LLM_MODEL")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    selfhosted_llm_url: str = Field(default="", alias="SELFHOSTED_LLM_URL")
    selfhosted_llm_model: str = Field(default="", alias="SELFHOSTED_LLM_MODEL")
    # API key for an OpenAI-compatible endpoint (OpenAI, Azure OpenAI, or a hosted gateway).
    # Sent as a Bearer header. Lives only in the analysis/worker service env (AGENTS.md #7).
    selfhosted_llm_api_key: str = Field(default="", alias="SELFHOSTED_LLM_API_KEY")

    # Auth
    jwt_secret: str = Field(default="", alias="JWT_SECRET")
    jwt_expire_hours: int = Field(default=8, alias="JWT_EXPIRE_HOURS")
    internal_service_token: str = Field(default="", alias="INTERNAL_SERVICE_TOKEN")

    # Limits
    max_upload_mb: int = Field(default=50, alias="MAX_UPLOAD_MB")
    sanitizer_timeout_seconds: int = Field(default=60, alias="SANITIZER_TIMEOUT_SECONDS")
    # sandboxed (default, requires bubblewrap + userns) | direct (DEMO ONLY: extraction runs
    # WITHOUT the no-network sandbox, for PaaS hosts that forbid user namespaces). `direct`
    # drops the containment guarantee (AGENTS.md #2) and is audited on every run.
    sanitizer_mode: str = Field(default="sandboxed", alias="SANITIZER_MODE")

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() in ("production", "prod")

    def _dsn(self, user: str, password: str, driver: str) -> str:
        return (
            f"postgresql+{driver}://{user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def app_dsn(self) -> str:
        """Async DSN for the runtime app role (INSERT+SELECT only on append-only tables)."""
        return self._dsn(self.app_user, self.app_password, "asyncpg")

    @property
    def migrator_dsn_sync(self) -> str:
        """Sync DSN for Alembic (migrator role owns DDL)."""
        return self._dsn(self.migrator_user, self.migrator_password, "psycopg2")


@lru_cache
def get_settings() -> Settings:
    return Settings()
