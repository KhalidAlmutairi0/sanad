"""Structural invariants proven by scanning the source tree.

INV-09: the research agent has no path to customer files (no imports of the app, no MinIO
        bucket credentials, no DB access from the agent package).
INV-12: secrets hygiene — the LLM/provider SDK is confined to services/llm; no provider SDK
        or LLM key reference leaks into the sanitizer or agent code.
Also: sandboxes never import apps (project-structure.md rule).
"""
from __future__ import annotations

import pathlib
import re

import pytest


def _find_repo() -> pathlib.Path | None:
    # Walk up to the repo root (marked by AGENTS.md). Returns None when the full tree is not
    # present (e.g. inside the api container, which only holds apps/api) — the equivalent
    # scan then runs as greps in the CI `static` job.
    here = pathlib.Path(__file__).resolve()
    for parent in (here, *here.parents):
        if (parent / "AGENTS.md").exists():
            return parent
    return None


REPO = _find_repo()
AGENT = REPO / "sandboxes" / "research-agent" if REPO else None
SANITIZER = REPO / "sandboxes" / "sanitizer" if REPO else None
API_APP = REPO / "apps" / "api" / "app" if REPO else None


def _require(path: pathlib.Path | None) -> pathlib.Path:
    if path is None or not path.exists():
        pytest.skip("full repo tree not present (running from a partial checkout/container)")
    return path


def _py_files(root: pathlib.Path) -> list[pathlib.Path]:
    return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]


def test_agent_does_not_import_app_or_touch_storage() -> None:
    # INV-09: the agent env cannot reach customer files. It must not import the app, nor
    # reference the MinIO client / quarantine or sanitized buckets / DB DSNs.
    forbidden = re.compile(
        r"\b(from app\b|import app\b|minio|boto3|s3|quarantine|sanitized|asyncpg|psycopg2|DATABASE_URL)\b",
        re.IGNORECASE,
    )
    agent = _require(AGENT)
    offenders = []
    for path in _py_files(agent):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if forbidden.search(line):
                offenders.append(f"{path.relative_to(REPO)}:{i}: {line.strip()}")
    assert not offenders, "agent env references file storage / DB / app:\n" + "\n".join(offenders)


def test_provider_sdk_confined_to_services_llm() -> None:
    # INV-12: no provider SDK import anywhere outside services/llm.
    sdk = re.compile(r"^\s*(from|import)\s+(anthropic|openai)\b", re.MULTILINE)
    api_app = _require(API_APP)
    offenders = []
    for path in _py_files(api_app):
        if "services/llm" in path.as_posix():
            continue
        if sdk.search(path.read_text(encoding="utf-8")):
            offenders.append(str(path.relative_to(REPO)))
    assert not offenders, "provider SDK imported outside services/llm: " + ", ".join(offenders)


def test_sanitizer_and_agent_have_no_llm_key_reference() -> None:
    # INV-12: the LLM API key lives only in the analysis/agent service env; the sanitizer
    # never sees it, and neither sandbox hardcodes any key.
    key_ref = re.compile(r"ANTHROPIC_API_KEY|api_key\s*=\s*['\"][A-Za-z0-9_\-]{12,}")
    for root in (_require(SANITIZER), _require(AGENT)):
        for path in _py_files(root):
            text = path.read_text(encoding="utf-8")
            assert not key_ref.search(text), f"LLM key reference in {path.relative_to(REPO)}"


def test_no_hardcoded_secrets_in_app_config() -> None:
    # INV-12: config reads from the environment; no literal secret assignments.
    literal_secret = re.compile(
        r"(password|secret|api_key|token)\s*=\s*['\"][A-Za-z0-9+/=_\-]{12,}['\"]",
        re.IGNORECASE,
    )
    api_app = _require(API_APP)
    offenders = []
    for path in _py_files(api_app):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "os.environ" in line or "Field(" in line or "get_settings" in line:
                continue
            if literal_secret.search(line):
                offenders.append(f"{path.relative_to(REPO)}:{i}")
    assert not offenders, "possible hardcoded secret: " + ", ".join(offenders)
