"""Per-source monitoring adapters (regulatory-monitoring pipeline).

Browser/network-free: exercises the registry, the Arabic article splitter, and the
enabled/adapter defaulting in load_sources. Live-site fetch/parse is verified separately.
"""
from __future__ import annotations

from app.services.monitoring import detection
from app.services.monitoring.adapters import adapter_names, get_adapter
from app.services.monitoring.adapters._text import split_arabic_articles


def test_registry_has_known_adapters_with_kinds():
    assert get_adapter("boe").kind == "html"
    assert get_adapter("moj").kind == "html"
    assert get_adapter("cma").kind == "html"
    assert get_adapter("uqn").kind == "pdf"
    for name in ("boe", "moj", "cma", "uqn"):
        assert get_adapter(name).robots_status  # every adapter documents its robots check
    assert set(adapter_names()) >= {"boe", "cma", "moj", "ncl", "uqn"}


def test_ncl_is_alias_for_boe():
    assert get_adapter("ncl") is get_adapter("boe")


def test_unknown_adapter_is_none():
    assert get_adapter("does-not-exist") is None


def test_split_arabic_articles_by_header():
    text = "ديباجة تمهيدية. المادة الأولى: نص الأولى. المادة الثانية: نص الثانية."
    arts = split_arabic_articles(text)
    refs = [a.article_ref for a in arts]
    assert refs == ["المادة الأولى", "المادة الثانية"]
    assert arts[0].text_ar.startswith("نص الأولى")


def test_split_returns_empty_without_headers():
    assert split_arabic_articles("نص عادي بدون أي عناوين مواد.") == []


def test_load_sources_excludes_disabled_and_defaults_adapter():
    sources = detection.load_sources()
    codes = {s["code"] for s in sources}
    # Disabled new adapters are not returned by run-check's source list.
    assert "MOJ-UPDATES" not in codes
    assert "CMA-RULEBOOK" not in codes
    assert "UQN-GAZETTE" not in codes
    # The existing 14 BOE laws are enabled and default to the boe adapter.
    assert "PDPL" in codes
    assert all(s.get("adapter", "boe") == "boe" for s in sources)
