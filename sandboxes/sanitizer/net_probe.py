"""Network-isolation probe. Runs INSIDE the sandbox via `run_sanitizer.sh --probe`.

Confirms the sandbox has NO egress. Exit 0 = isolated (every attempt failed as expected).
Exit 1 = LEAK (some attempt succeeded) — a hard failure of the isolation invariant.

Checks, in order:
  1. Only loopback network interfaces are visible.
  2. DNS resolution fails (no resolver reachable).
  3. Outbound TCP to public IPs fails immediately.
These hold regardless of whether the HOST has internet, so the test is CI-stable.
"""
from __future__ import annotations

import socket
import sys

LEAK = 1
ISOLATED = 0

PUBLIC_TARGETS = [("1.1.1.1", 443), ("8.8.8.8", 53), ("93.184.216.34", 80)]


def _interfaces_only_loopback() -> bool:
    # Enumerate the ACTUAL interfaces present in this network namespace. An isolated
    # (--unshare-net) namespace has only loopback. This inspects real kernel interfaces
    # rather than resolving the hostname, which would read a bind-mounted /etc/hosts and
    # false-positive on the container's own IP when the sandbox is nested inside Docker.
    for _index, name in socket.if_nameindex():
        if name != "lo":
            return False
    return True


def _dns_blocked() -> bool:
    for name in ("example.com", "sdaia.gov.sa", "cloudflare.com"):
        try:
            socket.getaddrinfo(name, 443)
            return False  # resolution succeeded -> egress path exists
        except socket.gaierror:
            continue
    return True


def _tcp_blocked() -> bool:
    for host, port in PUBLIC_TARGETS:
        try:
            with socket.create_connection((host, port), timeout=3):
                return False  # connected -> LEAK
        except OSError:
            continue
    return True


def main() -> int:
    leaks = []
    if not _interfaces_only_loopback():
        leaks.append("non-loopback interface visible")
    if not _dns_blocked():
        leaks.append("DNS resolution succeeded")
    if not _tcp_blocked():
        leaks.append("outbound TCP succeeded")

    if leaks:
        sys.stderr.write("SANITIZER EGRESS LEAK: " + "; ".join(leaks) + "\n")
        return LEAK
    sys.stdout.write("isolated: no interfaces, no DNS, no outbound TCP\n")
    return ISOLATED


if __name__ == "__main__":
    raise SystemExit(main())
