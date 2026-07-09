"""sanitize_contract job: quarantine file -> bubblewrap sandbox -> sanitized bucket.

Terminal-failure semantics (architecture.md 7c): timeout/OOM/unsupported are NOT retried;
the file is quarantined and the contract marked failed with a stable reason code + audit.
"""
from __future__ import annotations

import io
import os
import shutil
import tempfile
import uuid

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.storage import get_minio
from app.models import Contract
from app.services.audit import ACTOR_SANITIZER, write_audit
from app.services.sanitize import detect_extension, run_sanitizer

_settings = get_settings()


async def _mark_failed(session, contract: Contract, reason: str) -> None:
    contract.status = "failed"
    contract.failure_reason = reason
    await write_audit(
        session, actor=ACTOR_SANITIZER, action="sanitize_failed",
        target=str(contract.id), verdict="denied", detail={"reason": reason},
    )
    await session.commit()


async def sanitize_contract(ctx: dict, contract_id: str) -> str:
    async with SessionLocal() as session:
        contract = await session.get(Contract, uuid.UUID(contract_id))
        if not contract or contract.status != "sanitizing":
            return "skipped"

        await write_audit(
            session, actor=ACTOR_SANITIZER, action="sanitize_started",
            target=contract_id, verdict="n-a",
        )
        await session.commit()

        client = get_minio()
        tmp_dir = tempfile.mkdtemp(prefix="sanitize_")
        raw_path = os.path.join(tmp_dir, "raw.bin")
        try:
            client.fget_object(_settings.bucket_quarantine, contract.raw_object_key, raw_path)
            with open(raw_path, "rb") as fh:
                head = fh.read(8192)
            ext = detect_extension(head, raw_path)
            if ext is None:
                await _mark_failed(session, contract, "unsupported_file_type")
                return "unsupported_file_type"

            typed_path = os.path.join(tmp_dir, f"raw.{ext}")
            os.rename(raw_path, typed_path)

            result = run_sanitizer(
                typed_path, _settings.sanitizer_timeout_seconds, mode=_settings.sanitizer_mode
            )
            if not result.ok:
                await _mark_failed(session, contract, result.reason or "sanitize_failed")
                return result.reason or "sanitize_failed"

            sanitized_key = f"{contract_id}/sanitized.txt"
            text_bytes = (result.text or "").encode("utf-8")
            client.put_object(
                _settings.bucket_sanitized, sanitized_key,
                io.BytesIO(text_bytes), length=len(text_bytes),
                content_type="text/plain; charset=utf-8",
            )
            contract.sanitized_object_key = sanitized_key
            contract.status = "sanitized"
            await write_audit(
                session, actor=ACTOR_SANITIZER, action="sanitize_succeeded",
                target=contract_id, verdict="allowed",
                detail={
                    "sanitized_object_key": sanitized_key,
                    "chars": len(result.text or ""),
                    "sandboxed": result.sandboxed,  # False in DEMO direct mode
                },
            )
            await session.commit()
        finally:
            _cleanup(tmp_dir)

    # Continue the pipeline: extraction (deliverable 6).
    await ctx["redis"].enqueue_job("extract_clauses", contract_id)
    return "sanitized"


def _cleanup(path: str) -> None:
    shutil.rmtree(path, ignore_errors=True)
