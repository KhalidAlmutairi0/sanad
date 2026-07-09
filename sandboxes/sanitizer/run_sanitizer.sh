#!/usr/bin/env bash
# Upload Sanitizer wrapper (Sandbox A). Runs extraction inside bubblewrap with NO network.
#
# Containment (architecture.md §2, AGENTS.md #2):
#   --unshare-net   : no network namespace at all -> even successful code exec cannot reach
#                     anywhere; DNS resolution itself fails inside.
#   --unshare-pid/ipc/uts : process/IPC/host isolation.
#   --die-with-parent : sandbox dies if the worker dies.
#   read-only root, tmpfs scratch, raw file bind-mounted READ-ONLY at a fixed path.
#   rlimits (address space + CPU) + wall-clock timeout approximate cgroup caps. For
#   production, wrap this whole call in `systemd-run --scope -p MemoryMax=... -p CPUQuota=...`
#   to enforce true cgroup limits (see README).
#
# Usage:
#   run_sanitizer.sh <input_file>          -> extracted plain text to stdout
#   run_sanitizer.sh --probe               -> network-isolation self-test (exit 0 = isolated)
#
# Exit codes propagate from extract.py (0 ok, 2 unsupported, 3 error, 4 empty); 124 = timeout.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMEOUT="${SANITIZER_TIMEOUT_SECONDS:-60}"
MEM_KB="${SANITIZER_MEM_KB:-1048576}"   # 1 GiB address space cap
CPU_SEC="${SANITIZER_CPU_SECONDS:-30}"

if ! command -v bwrap >/dev/null 2>&1; then
  echo "bwrap (bubblewrap) not installed" >&2
  exit 3
fi

# Common bubblewrap flags: read-only host, isolated namespaces, no network.
bwrap_common=(
  bwrap
  --ro-bind / /
  --dev /dev
  --proc /proc
  --tmpfs /tmp
  --tmpfs /run
  --unshare-net
  --unshare-pid
  --unshare-ipc
  --unshare-uts
  --die-with-parent
  --new-session
  --clearenv
  --setenv PATH /usr/local/bin:/usr/bin:/bin
  --setenv PYTHONDONTWRITEBYTECODE 1
  --setenv HOME /tmp
)

apply_limits() {
  ulimit -v "$MEM_KB" || true   # address space
  ulimit -t "$CPU_SEC" || true  # CPU seconds
  ulimit -f 0 2>/dev/null || true  # no file writes to disk (tmpfs-only via bind is ro)
}
export -f apply_limits
export MEM_KB CPU_SEC

if [[ "${1:-}" == "--probe" ]]; then
  # Prove isolation: attempt DNS + outbound TCP; succeed (exit 0) ONLY if all attempts fail.
  exec timeout "$TIMEOUT" "${bwrap_common[@]}" \
    /usr/local/bin/python /sandboxes/sanitizer/net_probe.py
fi

INPUT="${1:?usage: run_sanitizer.sh <input_file>}"
[[ -f "$INPUT" ]] || { echo "input not found: $INPUT" >&2; exit 3; }

EXT="${INPUT##*.}"
SANDBOX_INPUT="/input/raw.${EXT}"   # fixed read-only path inside the sandbox

# Bind the raw file read-only at a fixed in-sandbox path; run extraction under rlimits.
exec timeout "$TIMEOUT" "${bwrap_common[@]}" \
  --ro-bind "$INPUT" "$SANDBOX_INPUT" \
  bash -c 'apply_limits; exec /usr/local/bin/python /sandboxes/sanitizer/extract.py "$1"' \
  _ "$SANDBOX_INPUT"
