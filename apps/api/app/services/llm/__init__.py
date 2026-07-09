"""The single LLM gateway. No provider SDK is imported anywhere outside this package.

Feature code builds an LLMRequest with trusted instructions and explicitly-typed
UntrustedBlocks; the provider is responsible for wrapping untrusted content in delimiters
and instructing the model to treat it as data. Feature code cannot bypass that.
"""
from app.services.llm.base import (
    LLMProvider,
    LLMRequest,
    UntrustedBlock,
    wrap_untrusted,
)
from app.services.llm.factory import get_llm

__all__ = ["LLMProvider", "LLMRequest", "UntrustedBlock", "wrap_untrusted", "get_llm"]
