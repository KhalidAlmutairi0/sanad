#!/usr/bin/env bash
# Governed Research Agent sandbox (Sandbox B) — network namespace with allowlisted egress.
# Reproduces the validated PoC (architecture.md §2). Run as root on Linux.
#
# Design:
#   - Dedicated netns `agent-ns` with its own veth pair + NAT to the host.
#   - nftables `output` chain with policy DROP: everything denied unless explicitly allowed.
#   - Allowed: loopback, established/related, DNS to the configured resolver, and TCP 443
#     ONLY to addresses in the dynamic set @allowed_ips (filled by update_allowlist.sh).
#   - IPv6 disabled inside the namespace (Happy Eyeballs otherwise causes silent hangs).
#   - Every denied packet is logged (prefix "AGENT-EGRESS-DENIED") for the audit pipeline.
set -euo pipefail

NS="${AGENT_NS:-agent-ns}"
VETH_HOST="${VETH_HOST:-veth-agent-h}"
VETH_NS="${VETH_NS:-veth-agent-n}"
SUBNET="${AGENT_SUBNET:-10.200.200.0/30}"
HOST_IP="${AGENT_HOST_IP:-10.200.200.1}"
NS_IP="${AGENT_NS_IP:-10.200.200.2}"
RESOLVER="${AGENT_RESOLVER:-1.1.1.1}"
UPLINK="${AGENT_UPLINK:-$(ip route show default | awk '/default/ {print $5; exit}')}"

if [[ $EUID -ne 0 ]]; then echo "must run as root" >&2; exit 1; fi

echo "[agent-ns] creating namespace $NS"
ip netns add "$NS" 2>/dev/null || true

# veth pair: one end on host, one inside the namespace.
ip link add "$VETH_HOST" type veth peer name "$VETH_NS" 2>/dev/null || true
ip link set "$VETH_NS" netns "$NS"

ip addr add "$HOST_IP/30" dev "$VETH_HOST" 2>/dev/null || true
ip link set "$VETH_HOST" up
ip netns exec "$NS" ip addr add "$NS_IP/30" dev "$VETH_NS" 2>/dev/null || true
ip netns exec "$NS" ip link set "$VETH_NS" up
ip netns exec "$NS" ip link set lo up
ip netns exec "$NS" ip route add default via "$HOST_IP"

# Disable IPv6 inside the namespace (removes the Happy-Eyeballs silent-timeout failure class).
ip netns exec "$NS" sysctl -qw net.ipv6.conf.all.disable_ipv6=1
ip netns exec "$NS" sysctl -qw net.ipv6.conf.default.disable_ipv6=1

# Host-side NAT so allowed traffic can reach the internet.
sysctl -qw net.ipv4.ip_forward=1
nft list table ip agent-nat >/dev/null 2>&1 || nft add table ip agent-nat
nft flush table ip agent-nat
nft add chain ip agent-nat postrouting '{ type nat hook postrouting priority 100 ; }'
nft add rule ip agent-nat postrouting ip saddr "$SUBNET" oif "$UPLINK" masquerade

# In-namespace egress firewall: default DROP, allow only the narrow set below.
ip netns exec "$NS" nft flush ruleset
ip netns exec "$NS" nft add table inet filter
ip netns exec "$NS" nft add chain inet filter output '{ type filter hook output priority 0 ; policy drop ; }'
# Named set of allowed destination IPs, refreshed by the DNS watcher.
ip netns exec "$NS" nft add set inet filter allowed_ips '{ type ipv4_addr ; flags interval ; }'
ip netns exec "$NS" nft add rule inet filter output oif lo accept
ip netns exec "$NS" nft add rule inet filter output ct state established,related accept
ip netns exec "$NS" nft add rule inet filter output ip daddr "$RESOLVER" udp dport 53 accept
ip netns exec "$NS" nft add rule inet filter output ip daddr "$RESOLVER" tcp dport 53 accept
ip netns exec "$NS" nft add rule inet filter output ip daddr @allowed_ips tcp dport 443 accept
# Everything else: log (for audit) then drop (policy).
ip netns exec "$NS" nft add rule inet filter output log prefix '"AGENT-EGRESS-DENIED "' level info
# Block all IPv6 outright as a belt-and-braces measure.
ip netns exec "$NS" nft add chain inet filter output6 '{ type filter hook output priority 0 ; }' 2>/dev/null || true

echo "[agent-ns] ready. resolver=$RESOLVER uplink=$UPLINK subnet=$SUBNET"
echo "[agent-ns] populate the allowlist:  AGENT_NS=$NS ./update_allowlist.sh"
