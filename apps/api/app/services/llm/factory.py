"""Provider selection from config. LLM_PROVIDER=anthropic|selfhosted."""
from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.services.llm.base import LLMProvider


@lru_cache
def get_llm() -> LLMProvider:
    s = get_settings()
    if s.llm_provider == "anthropic":
        from app.services.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(api_key=s.anthropic_api_key, model=s.llm_model)
    if s.llm_provider == "selfhosted":
        from app.services.llm.selfhosted_provider import SelfHostedProvider

        return SelfHostedProvider(url=s.selfhosted_llm_url, model=s.selfhosted_llm_model)
    raise ValueError(f"Unknown LLM_PROVIDER: {s.llm_provider!r}")
