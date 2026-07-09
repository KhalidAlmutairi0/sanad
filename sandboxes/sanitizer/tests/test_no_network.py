"""PROVES the upload sanitizer has no network egress (AGENTS.md #2, invariant test).

Runs the actual sandbox wrapper (`run_sanitizer.sh --probe`), which executes net_probe.py
inside bubblewrap with --unshare-net. The probe exits 0 only if every egress attempt fails.

Skips (does not fail) when bubblewrap is unavailable, so the suite runs anywhere; in the
api/worker image bwrap is installed and this test runs for real.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
RUNNER = HERE / "run_sanitizer.sh"


requires_bwrap = pytest.mark.skipif(
    shutil.which("bwrap") is None, reason="bubblewrap not installed in this environment"
)


def _skip_if_no_userns(result: subprocess.CompletedProcess) -> None:
    # bwrap needs unprivileged user namespaces. Some CI/container hosts disable them; that
    # is an environment limitation, not an isolation leak, so skip rather than fail.
    markers = ("setting up uid map", "user namespace", "clone", "Operation not permitted", "No permission")
    if result.returncode != 0 and any(m.lower() in result.stderr.lower() for m in markers):
        pytest.skip(f"user namespaces unavailable here: {result.stderr.strip()}")


@requires_bwrap
def test_sanitizer_has_no_network_egress() -> None:
    result = subprocess.run(
        ["bash", str(RUNNER), "--probe"],
        capture_output=True,
        text=True,
        timeout=90,
    )
    _skip_if_no_userns(result)
    # Exit 0 == isolated. rc==1 (LEAK) or any other code fails the invariant.
    assert result.returncode == 0, (
        f"sanitizer egress isolation FAILED (rc={result.returncode}): "
        f"{result.stdout}\n{result.stderr}"
    )
    assert "isolated" in result.stdout


@requires_bwrap
def test_sanitizer_extracts_txt_to_plain_text(tmp_path: pathlib.Path) -> None:
    sample = tmp_path / "contract.txt"
    sample.write_text("البند الأول: تُعالَج البيانات بموافقة صاحبها.\n", encoding="utf-8")
    result = subprocess.run(
        ["bash", str(RUNNER), str(sample)],
        capture_output=True,
        text=True,
        timeout=90,
    )
    _skip_if_no_userns(result)
    assert result.returncode == 0, result.stderr
    assert "البند الأول" in result.stdout
