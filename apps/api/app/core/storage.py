"""MinIO (S3) client. Quarantine + sanitized buckets, server-side encryption assumed set
at bucket level by infra. Presigned PUT/GET used for uploads and reads."""
from __future__ import annotations

from datetime import timedelta

from minio import Minio

from app.core.config import get_settings

_settings = get_settings()


def get_minio() -> Minio:
    return Minio(
        _settings.minio_endpoint,
        access_key=_settings.minio_root_user,
        secret_key=_settings.minio_root_password,
        secure=_settings.minio_use_ssl,
    )


def presigned_put(bucket: str, key: str, expires_seconds: int = 3600) -> str:
    """Presigned PUT URL, rewritten to the browser-reachable endpoint."""
    client = get_minio()
    url = client.presigned_put_object(bucket, key, expires=timedelta(seconds=expires_seconds))
    return _rewrite_public(url)


def presigned_get(bucket: str, key: str, expires_seconds: int = 3600) -> str:
    client = get_minio()
    url = client.presigned_get_object(bucket, key, expires=timedelta(seconds=expires_seconds))
    return _rewrite_public(url)


def _rewrite_public(url: str) -> str:
    """Internal endpoint (minio:9000) -> browser-reachable endpoint (localhost:9000)."""
    return url.replace(f"//{_settings.minio_endpoint}/", f"//{_settings.minio_public_endpoint}/", 1)


def storage_healthy() -> bool:
    try:
        client = get_minio()
        client.bucket_exists(_settings.bucket_quarantine)
        return True
    except Exception:
        return False
