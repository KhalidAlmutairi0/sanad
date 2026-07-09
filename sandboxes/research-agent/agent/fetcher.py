"""Research agent fetcher. Runs INSIDE the egress-controlled namespace (Sandbox B).

Defense in depth: the nftables policy-drop is the hard boundary, but the fetcher ALSO
refuses any URL whose host is not in allowlist.yaml. The agent never receives customer
files or contract text — it only pulls official regulatory pages.
"""
from __future__ import annotations

import hashlib
import pathlib
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
import yaml

ALLOWLIST = pathlib.Path(__file__).resolve().parents[1] / "allowlist.yaml"


def _allowed_domains() -> set[str]:
    spec = yaml.safe_load(ALLOWLIST.read_text(encoding="utf-8"))
    return {d.strip().lower() for d in spec.get("domains", [])}


def _host_allowed(host: str, allowed: set[str]) -> bool:
    host = host.lower()
    return any(host == d or host.endswith(f".{d}") for d in allowed)


@dataclass
class FetchResult:
    url: str
    status: int
    content: str
    content_hash: str


def fetch(url: str, *, timeout: float = 20.0) -> FetchResult:
    allowed = _allowed_domains()
    host = urlparse(url).hostname or ""
    if not _host_allowed(host, allowed):
        raise PermissionError(f"host not in allowlist: {host}")

    with httpx.Client(timeout=timeout, follow_redirects=False) as client:
        resp = client.get(url)
    text = resp.text
    return FetchResult(
        url=url,
        status=resp.status_code,
        content=text,
        content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )
