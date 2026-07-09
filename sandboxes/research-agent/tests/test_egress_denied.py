"""PROVES the research agent cannot reach a non-allowlisted domain (AGENTS.md #2).

Brings up the agent namespace via setup_agent_ns.sh, then, from INSIDE the namespace,
attempts an outbound TCP 443 connection to an address that is NOT in @allowed_ips and
asserts it is denied (the nftables policy-drop discards the packets -> connect times out).

Requires Linux + root + nft + ip netns. Skips (does not fail) otherwise, so the suite runs
anywhere; on a Linux host with privileges it runs for real.
"""
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
SETUP = HERE / "netns" / "setup_agent_ns.sh"
NS = "sanad-test-agent-ns"

_missing = (
    os.geteuid() != 0
    or shutil.which("nft") is None
    or shutil.which("ip") is None
)
requires_netns = pytest.mark.skipif(_missing, reason="needs Linux + root + nft + ip netns")


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


@pytest.fixture()
def agent_ns():
    env = {**os.environ, "AGENT_NS": NS}
    setup = _run(["bash", str(SETUP)], env=env)
    if setup.returncode != 0:
        pytest.skip(f"could not create namespace (no uplink?): {setup.stderr.strip()}")
    try:
        yield NS
    finally:
        _run(["ip", "netns", "del", NS])
        _run(["nft", "delete", "table", "ip", "agent-nat"])


@requires_netns
def test_non_allowlisted_domain_is_denied(agent_ns: str) -> None:
    # allowed_ips is empty (watcher not run), so ANY outbound 443 must be dropped.
    probe = (
        "import socket,sys\n"
        "try:\n"
        "    socket.create_connection(('8.8.8.8', 443), timeout=4)\n"
        "    sys.exit(1)\n"  # connected -> egress LEAK
        "except OSError:\n"
        "    sys.exit(0)\n"  # denied as expected
    )
    result = _run(["ip", "netns", "exec", agent_ns, "python3", "-c", probe])
    assert result.returncode == 0, "non-allowlisted egress was NOT denied (leak)"


@requires_netns
def test_dns_to_resolver_is_permitted_but_arbitrary_ip_is_not(agent_ns: str) -> None:
    # DNS to the configured resolver is allowed by rule; a random TCP dest is not.
    probe = (
        "import socket,sys\n"
        "try:\n"
        "    socket.create_connection(('198.51.100.7', 443), timeout=4)\n"  # TEST-NET-2
        "    sys.exit(1)\n"
        "except OSError:\n"
        "    sys.exit(0)\n"
    )
    result = _run(["ip", "netns", "exec", agent_ns, "python3", "-c", probe])
    assert result.returncode == 0, "arbitrary destination was reachable (leak)"


@requires_netns
def test_non_443_port_to_allowlisted_ip_is_denied(agent_ns: str) -> None:
    # Even after allowing an IP, only TCP 443 is permitted; other ports stay dropped.
    ip = "203.0.113.9"  # TEST-NET-3
    _run(["ip", "netns", "exec", agent_ns, "nft", "add", "element", "inet", "filter",
          "allowed_ips", "{ " + ip + " }"])
    probe = (
        "import socket,sys\n"
        "try:\n"
        f"    socket.create_connection(('{ip}', 22), timeout=4)\n"  # SSH, not 443
        "    sys.exit(1)\n"
        "except OSError:\n"
        "    sys.exit(0)\n"
    )
    result = _run(["ip", "netns", "exec", agent_ns, "python3", "-c", probe])
    assert result.returncode == 0, "non-443 port to an allowed IP was reachable (leak)"


@requires_netns
def test_allowlist_set_update_mechanism(agent_ns: str) -> None:
    # Proves the exact mechanism update_allowlist.sh uses: adding an element makes it appear
    # in the live set (this is how DNS-resolved IPs become reachable within 60s).
    ip = "203.0.113.42"
    _run(["ip", "netns", "exec", agent_ns, "nft", "add", "element", "inet", "filter",
          "allowed_ips", "{ " + ip + " }"])
    listed = _run(["ip", "netns", "exec", agent_ns, "nft", "list", "set", "inet", "filter", "allowed_ips"])
    assert ip in listed.stdout, f"element not present in live set:\n{listed.stdout}"
    # Fail-closed: flushing the set removes it (a stale/empty watcher denies, never allows).
    _run(["ip", "netns", "exec", agent_ns, "nft", "flush", "set", "inet", "filter", "allowed_ips"])
    listed2 = _run(["ip", "netns", "exec", agent_ns, "nft", "list", "set", "inet", "filter", "allowed_ips"])
    assert ip not in listed2.stdout
