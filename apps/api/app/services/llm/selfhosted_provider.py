"""Self-hosted / stub provider.

Two modes, both air-gapped (no Anthropic SDK):
  - If SELFHOSTED_LLM_URL is set, POST to an OpenAI-compatible /chat/completions endpoint
    (the sovereign, fully on-prem model option).
  - Otherwise act as a deterministic STUB: return the caller-supplied `offline_stub`. This
    keeps `docker compose up` and the test suite fully functional with no external model,
    while every downstream invariant (citation gate, review gates) still runs for real.
"""
from __future__ import annotations

import json

import httpx

from app.services.llm.base import LLMProvider, LLMRequest


class SelfHostedProvider(LLMProvider):
    def __init__(self, url: str | None, model: str | None) -> None:
        self._url = url or None
        self._model = model or "local"

    async def complete(self, req: LLMRequest) -> str:
        if self._url:
            return await self._call_endpoint(req)
        return self._stub(req)

    async def _call_endpoint(self, req: LLMRequest) -> str:
        payload = {
            "model": self._model,
            "temperature": req.temperature,
            "max_tokens": req.max_tokens,
            "messages": [
                {"role": "system", "content": req.render_system()},
                {"role": "user", "content": req.render_user()},
            ],
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self._url.rstrip('/')}/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]

    @staticmethod
    def _stub(req: LLMRequest) -> str:
        if req.offline_stub is None:
            return ""
        if isinstance(req.offline_stub, str):
            return req.offline_stub
        return json.dumps(req.offline_stub, ensure_ascii=False)
