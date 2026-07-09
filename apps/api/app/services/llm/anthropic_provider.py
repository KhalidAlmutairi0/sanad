"""Anthropic provider. The ONLY place the anthropic SDK is imported.

The API key lives only in this service's environment (AGENTS.md #7), never in the frontend
or sanitizer. Egress to the LLM domain goes through the governed path on-prem.
"""
from __future__ import annotations

from anthropic import AsyncAnthropic

from app.services.llm.base import LLMProvider, LLMRequest


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for the anthropic provider")
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def complete(self, req: LLMRequest) -> str:
        resp = await self._client.messages.create(
            model=self._model,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            system=req.render_system(),
            messages=[{"role": "user", "content": req.render_user()}],
        )
        return "".join(block.text for block in resp.content if block.type == "text")
