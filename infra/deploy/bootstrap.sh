#!/usr/bin/env bash
# Provision a fresh Ubuntu 22.04/24.04 cloud VM to run SANAD.
# Installs Docker + Compose, enables the kernel features the sandboxes need, and locks the
# firewall to 22 + 80 + 443 (data services stay internal to the Docker network). Run as root.
set -euo pipefail

if [[ $EUID -ne 0 ]]; then echo "run as root (sudo)"; exit 1; fi

echo "[1/5] base packages + Docker"
apt-get update
apt-get install -y ca-certificates curl gnupg nftables ufw
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker

echo "[2/5] enable unprivileged user namespaces (bubblewrap sanitizer needs them)"
cat > /etc/sysctl.d/99-sanad.conf <<'SYSCTL'
kernel.unprivileged_userns_clone=1
net.ipv4.ip_forward=1
SYSCTL
sysctl --system >/dev/null

echo "[3/5] firewall: allow SSH + HTTP(S) only; data ports stay on the internal docker net"
ufw --force reset >/dev/null
ufw default deny incoming >/dev/null
ufw default allow outgoing >/dev/null
ufw allow 22/tcp >/dev/null
ufw allow 80/tcp >/dev/null
ufw allow 443/tcp >/dev/null
ufw --force enable >/dev/null

echo "[4/5] research-agent egress sandbox: nftables available; install the allowlist timer"
if [[ -d /opt/sanad/sandboxes/research-agent/netns ]]; then
  cp /opt/sanad/sandboxes/research-agent/netns/agent-allowlist.{service,timer} /etc/systemd/system/ || true
  systemctl daemon-reload
  echo "  -> run setup_agent_ns.sh once, then: systemctl enable --now agent-allowlist.timer"
else
  echo "  -> place the repo at /opt/sanad, then re-run this step (see docs/deploy.md)"
fi

echo "[5/5] done. Next: docs/deploy.md — fill infra/.env, then docker compose up."
