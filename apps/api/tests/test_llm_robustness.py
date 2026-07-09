"""LLM output robustness (test-plan §11 REL-04 flavour): malformed model output is handled,
never persisted as a silent success. No network/DB needed."""
from __future__ import annotations

import pytest

from app.services.llm.base import LLMProvider, LLMRequest


class _Provider(LLMProvider):
    def __init__(self, outputs: list[str]) -> None:
        self._outputs = outputs
        self._i = 0

    async def complete(self, req: LLMRequest) -> str:  # noqa: ARG002
        out = self._outputs[min(self._i, len(self._outputs) - 1)]
        self._i += 1
        return out


async def test_complete_json_recovers_from_one_bad_parse() -> None:
    # First response is junk, second is valid — complete_json retries once and succeeds.
    p = _Provider(["not json at all", '{"ok": true}'])
    assert await p.complete_json(LLMRequest(system_prompt="s", instruction="i")) == {"ok": True}


async def test_complete_json_raises_on_persistent_garbage() -> None:
    p = _Provider(["garbage", "still garbage"])
    with pytest.raises(ValueError):
        await p.complete_json(LLMRequest(system_prompt="s", instruction="i"))


async def test_complete_json_extracts_from_fenced_and_noisy_output() -> None:
    p = _Provider(["Here you go:\n```json\n[1, 2, 3]\n```\nThanks"])
    assert await p.complete_json(LLMRequest(system_prompt="s", instruction="i")) == [1, 2, 3]
