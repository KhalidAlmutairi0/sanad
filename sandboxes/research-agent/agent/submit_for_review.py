"""Submit a fetched article candidate to the human verification queue.

The agent NEVER writes to regulation_versions directly (append-only, human gate). It POSTs
the candidate to the API's internal endpoint, which records it for human verification.
Auth is the deployment-local internal service token (env only, never logged).
"""
from __future__ import annotations

import os

import httpx

API_BASE = os.environ.get("API_BASE_URL", "http://api:8000") + "/api/v1"
INTERNAL_TOKEN = os.environ.get("INTERNAL_SERVICE_TOKEN", "")


def submit_candidate(
    *, regulation_code: str, article_ref: str, article_text_ar: str, source_url: str, change_type: str
) -> dict:
    if not INTERNAL_TOKEN:
        raise RuntimeError("INTERNAL_SERVICE_TOKEN not set")
    payload = {
        "regulation_code": regulation_code,
        "article_ref": article_ref,
        "article_text_ar": article_text_ar,
        "source_url": source_url,
        "change_type": change_type,
    }
    with httpx.Client(timeout=20.0) as client:
        resp = client.post(
            f"{API_BASE}/internal/agent-candidate",
            json=payload,
            headers={"x-internal-token": INTERNAL_TOKEN},
        )
        resp.raise_for_status()
        return resp.json()
