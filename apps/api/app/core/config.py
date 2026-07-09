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

    # LLM (behind services/llm only)
    llm_provider: str = Field(default="selfhosted", alias="LLM_PROVIDER")
    llm_model: str = Field(default="claude-sonnet-4-20250514", alias="LLM_MODEL")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    selfhosted_llm_url: str = Field(default="", alias="SELFHOSTED_LLM_URL")
    selfhosted_llm_model: str = Field(default="", alias="SELFHOSTED_LLM_MODEL")

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
