"""MinIO (S3) client. Quarantine + sanitized buckets, server-side encryption assumed set
at bucket level by infra. Presigned PUT/GET used for uploads and reads."""
from __future__ import annotations

from datetime import timedelta

from minio import Minio

from app.core.config import get_settings

_settings = get_settings()


def get_minio() -> Minio:
    """Internal client for server-side object I/O (workers put/get via the docker network)."""
    return Minio(
        _settings.minio_endpoint,
        access_key=_settings.minio_root_user,
        secret_key=_settings.minio_root_password,
        secure=_settings.minio_use_ssl,
    )


def _public_client() -> Minio:
    """Client pointed at the browser-facing endpoint. Used ONLY to sign presigned URLs, so
    the signed Host header matches what the browser actually sends (SigV4 signs Host)."""
    return Minio(
        _settings.minio_public_endpoint,
        access_key=_settings.minio_root_user,
        secret_key=_settings.minio_root_password,
        secure=_settings.minio_public_secure,
    )


def presigned_put(bucket: str, key: str, expires_seconds: int = 3600) -> str:
    return _public_client().presigned_put_object(bucket, key, expires=timedelta(seconds=expires_seconds))


def presigned_get(bucket: str, key: str, expires_seconds: int = 3600) -> str:
    return _public_client().presigned_get_object(bucket, key, expires=timedelta(seconds=expires_seconds))


def storage_healthy() -> bool:
    try:
        client = get_minio()
        client.bucket_exists(_settings.bucket_quarantine)
        return True
    except Exception:
        return False
