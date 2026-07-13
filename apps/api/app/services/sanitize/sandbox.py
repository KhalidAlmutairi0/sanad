"""Invoke the upload sanitizer (bubblewrap) as a subprocess and interpret its result.

File type is detected from CONTENT (magic bytes), not a client-supplied name, then the raw
bytes are written to a temp file with the right extension for the sandbox to bind read-only.
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
import zipfile
from dataclasses import dataclass

logger = logging.getLogger(__name__)

SANITIZER_DIR = os.environ.get("SANITIZER_DIR", "/sandboxes/sanitizer")
RUNNER = os.path.join(SANITIZER_DIR, "run_sanitizer.sh")
EXTRACT = os.path.join(SANITIZER_DIR, "extract.py")

# extract.py exit codes -> stable reason codes (api-contracts.md).
_RC_REASON = {2: "unsupported_file_type", 3: "sanitize_failed", 4: "sanitize_failed", 124: "sanitize_timeout"}


@dataclass
class SanitizeResult:
    ok: bool
    text: str | None = None
    reason: str | None = None  # stable reason code when not ok
    sandboxed: bool = True  # False when extraction ran in DEMO `direct` mode (no isolation)
    ocr_used: bool = False  # True when the PDF had no text layer and was OCR'd


def detect_extension(data: bytes, path: str) -> str | None:
    """Return 'pdf' | 'docx' | 'txt' from content, or None if unsupported."""
    if data[:5] == b"%PDF-":
        return "pdf"
    if data[:4] == b"PK\x03\x04":
        try:
            with zipfile.ZipFile(path) as zf:
                if "word/document.xml" in zf.namelist():
                    return "docx"
        except zipfile.BadZipFile:
            return None
        return None
    try:
        data.decode("utf-8")
        return "txt"
    except UnicodeDecodeError:
        return None


def run_sanitizer(input_path: str, timeout_seconds: int, *, mode: str = "sandboxed") -> SanitizeResult:
    """Run extraction on `input_path`. Returns clean text or a stable reason code.

    mode="sandboxed" (default): inside bubblewrap with no network (the real guarantee).
    mode="direct" (DEMO ONLY): runs extract.py with no sandbox, for PaaS hosts without user
    namespaces. This drops the containment guarantee; it is flagged on the result and audited.

    Timeout/error verdicts are terminal (the caller must NOT retry — a file that kills the
    sandbox is quarantined and flagged, architecture.md 7c)."""
    sandboxed = mode != "direct"
    if sandboxed:
        cmd = ["bash", RUNNER, input_path]
    else:
        logger.warning("SANITIZER RUNNING UNSANDBOXED (SANITIZER_MODE=direct) — demo only, "
                       "no network containment for %s", input_path)
        cmd = [sys.executable, EXTRACT, input_path]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds + 5)
    except subprocess.TimeoutExpired:
        return SanitizeResult(ok=False, reason="sanitize_timeout", sandboxed=sandboxed)

    ocr_used = "OCR_USED" in (proc.stderr or "")
    if proc.returncode == 0:
        return SanitizeResult(ok=True, text=proc.stdout, sandboxed=sandboxed, ocr_used=ocr_used)
    return SanitizeResult(ok=False, reason=_RC_REASON.get(proc.returncode, "sanitize_failed"), sandboxed=sandboxed)
