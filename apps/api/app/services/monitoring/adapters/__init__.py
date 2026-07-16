"""Per-source adapter registry. `adapter:` in _sources.yaml selects one of these by name.

'ncl' (National Center for Legislation) is an alias for the BOE adapter: that function resolves
to the Bureau of Experts legislation database (laws.boe.gov.sa), which the BOE adapter already
handles — there is no separate NCL site to crawl.
"""
from __future__ import annotations

from app.services.monitoring.adapters.base import Article, SourceAdapter
from app.services.monitoring.adapters.boe import BoeAdapter
from app.services.monitoring.adapters.cma import CmaAdapter
from app.services.monitoring.adapters.moj import MojAdapter
from app.services.monitoring.adapters.uqn import UqnAdapter

_ADAPTERS: dict[str, SourceAdapter] = {}


def _register(adapter: SourceAdapter) -> None:
    _ADAPTERS[adapter.name] = adapter


for _a in (BoeAdapter(), MojAdapter(), CmaAdapter(), UqnAdapter()):
    _register(_a)
_ADAPTERS["ncl"] = _ADAPTERS["boe"]  # alias


def get_adapter(name: str) -> SourceAdapter | None:
    return _ADAPTERS.get(name)


def adapter_names() -> list[str]:
    return sorted(_ADAPTERS)


__all__ = ["Article", "SourceAdapter", "get_adapter", "adapter_names"]
