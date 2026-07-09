"""Sanitize orchestration helpers. The worker (analysis env) invokes the bubblewrap
sandbox as a subprocess; the worker process itself stays OUTSIDE the sandbox
(architecture.md 7c)."""
from app.services.sanitize.sandbox import SanitizeResult, detect_extension, run_sanitizer

__all__ = ["SanitizeResult", "detect_extension", "run_sanitizer"]
