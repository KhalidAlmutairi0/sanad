"""Invoke the upload sanitizer (bubblewrap) as a subprocess and interpret its result.

File type is detected from CONTENT (magic bytes), not a client-supplied name, then the raw
bytes are written to a temp file with the right extension for the sandbox to bind read-only.
"""
from __future__ import annotations

import os
import subprocess
import zipfile
from dataclasses import dataclass

SANITIZER_DIR = os.environ.get("SANITIZER_DIR", "/sandboxes/sanitizer")
RUNNER = os.path.join(SANITIZER_DIR, "run_sanitizer.sh")

# extract.py exit codes -> stable reason codes (api-contracts.md).
_RC_REASON = {2: "unsupported_file_type", 3: "sanitize_failed", 4: "sanitize_failed", 124: "sanitize_timeout"}


@dataclass
class SanitizeResult:
    ok: bool
    text: str | None = None
    reason: str | None = None  # stable reason code when not ok


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


def run_sanitizer(input_path: str, timeout_seconds: int) -> SanitizeResult:
    """Run the sandbox on `input_path`. Returns clean text or a stable reason code.

    Timeout/error verdicts are terminal (the caller must NOT retry — a file that kills the
    sandbox is quarantined and flagged, architecture.md 7c)."""
    try:
        proc = subprocess.run(
            ["bash", RUNNER, input_path],
            capture_output=True,
            text=True,
            timeout=timeout_seconds + 5,  # outer guard; bwrap has its own `timeout`
        )
    except subprocess.TimeoutExpired:
        return SanitizeResult(ok=False, reason="sanitize_timeout")

    if proc.returncode == 0:
        return SanitizeResult(ok=True, text=proc.stdout)
    return SanitizeResult(ok=False, reason=_RC_REASON.get(proc.returncode, "sanitize_failed"))
