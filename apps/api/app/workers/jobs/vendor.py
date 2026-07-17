"""evaluate_vendor_batch job: for each vendor submission, sanitize the raw file (bwrap) then run
Sandbox-1 extraction + Stage-1 gate. Runs in the worker (which holds the sandbox privileges), not
the API. Resumable: submissions already extracted are skipped."""
from __future__ import annotations

import os
import shutil
import tempfile
import uuid

from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.storage import get_minio
from app.models import VendorEvaluation, VendorSubmission
from app.services.sanitize.sandbox import detect_extension, run_sanitizer
from app.services.vendor.orchestrate import extract_and_gate

_settings = get_settings()
ACTOR = "analysis"


async def evaluate_vendor_batch(ctx: dict, evaluation_id: str) -> str:  # noqa: ARG001
    async with SessionLocal() as session:
        ev = await session.get(VendorEvaluation, uuid.UUID(evaluation_id))
        if not ev or ev.status != "comparing":
            return "skipped"
        subs = (
            await session.execute(
                select(VendorSubmission).where(VendorSubmission.evaluation_id == ev.id)
            )
        ).scalars().all()

        client = get_minio()
        for sub in subs:
            if sub.extraction is not None:  # resumable — already processed
                continue
            tmp = tempfile.mkdtemp(prefix="vendor_")
            raw_path = os.path.join(tmp, "raw.bin")
            try:
                client.fget_object(_settings.bucket_quarantine, sub.raw_object_key, raw_path)
                with open(raw_path, "rb") as fh:
                    head = fh.read(8192)
                ext = detect_extension(head, raw_path)
                if ext is None:
                    sub.status = "failed"
                    await session.commit()
                    continue
                typed = os.path.join(tmp, f"raw.{ext}")
                os.rename(raw_path, typed)
                result = run_sanitizer(
                    typed, _settings.sanitizer_timeout_seconds, mode=_settings.sanitizer_mode
                )
                if not result.ok:
                    sub.status = "failed"
                    await session.commit()
                    continue
                await extract_and_gate(session, sub, result.text or "", actor=ACTOR)
                await session.commit()
            except Exception:  # noqa: BLE001 — one bad file must not abort the batch
                sub.status = "failed"
                await session.commit()
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

        ev.status = "done"
        await session.commit()
    return "done"
