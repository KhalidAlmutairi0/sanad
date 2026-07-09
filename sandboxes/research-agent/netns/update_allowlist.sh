#!/usr/bin/env bash
# DNS watcher: resolve allowlist.yaml domains and refresh the nftables @allowed_ips set
# inside the agent namespace. Run every 60s by agent-allowlist.timer.
#
# Empirically required: CDN-backed domains rotate IPs within minutes; a static IP rule
# breaks silently. Re-resolving on a timer keeps the allowlist correct (validated PoC).
set -euo pipefail

NS="${AGENT_NS:-agent-ns}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALLOWLIST="${AGENT_ALLOWLIST:-$HERE/../allowlist.yaml}"
RESOLVER="${AGENT_RESOLVER:-1.1.1.1}"

if [[ $EUID -ne 0 ]]; then echo "must run as root" >&2; exit 1; fi
command -v getent >/dev/null 2>&1 || true

# Extract domains from the YAML (robust across awk implementations; agent env has python3).
mapfile -t DOMAINS < <(python3 -c "import yaml,sys; print('\n'.join(yaml.safe_load(open(sys.argv[1]))['domains']))" "$ALLOWLIST")

declare -A ips
for d in "${DOMAINS[@]}"; do
  [[ -z "$d" ]] && continue
  # A records only (IPv6 is disabled in the namespace). Use the configured resolver.
  while read -r ip; do
    [[ "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] && ips["$ip"]=1
  done < <(getent ahostsv4 "$d" 2>/dev/null | awk '{print $1}' | sort -u \
           || nslookup -type=A "$d" "$RESOLVER" 2>/dev/null | awk '/^Address: /{print $2}')
done

if [[ ${#ips[@]} -eq 0 ]]; then
  echo "[allowlist] WARNING: resolved 0 IPs; leaving existing set unchanged" >&2
  exit 0
fi

# Atomic-ish refresh: flush the set, add the freshly resolved elements.
ip netns exec "$NS" nft flush set inet filter allowed_ips
elements=$(IFS=,; echo "${!ips[*]}")
ip netns exec "$NS" nft add element inet filter allowed_ips "{ $elements }"

echo "[allowlist] refreshed ${#ips[@]} IP(s) for ${#DOMAINS[@]} domain(s) in $NS"
