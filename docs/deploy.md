# deploy.md — SANAD on a cloud VM

Target: one Ubuntu 22.04/24.04 VM you control (the sandboxes need Linux kernel features —
user namespaces, network namespaces, nftables, systemd — so a managed "serverless" host is
not enough). Managed Postgres/object storage can replace the containers; see the last
section. This runbook deploys the full stack with the offline **stub LLM** (wire a real
model later).

## 0. Prerequisites

- A VM (2 vCPU / 4–8 GB RAM min; the embedder + LLM later want more), SSH access.
- Two DNS A records at the VM's public IP:
  - `sanad.example.com` → the app
  - `storage.sanad.example.com` → MinIO (browsers upload/download via presigned URLs)
- Cloud security group: allow inbound 22, 80, 443 only.

## 1. Provision the host

```bash
sudo mkdir -p /opt/sanad && sudo chown "$USER" /opt/sanad
git clone https://github.com/KhalidAlmutairi0/sanad.git /opt/sanad
cd /opt/sanad
sudo bash infra/deploy/bootstrap.sh   # Docker + userns + firewall + agent timer units
```

## 2. Configure secrets

```bash
cp infra/.env.production.example infra/.env
# Edit infra/.env: set DOMAIN + MINIO_DOMAIN and every __CHANGE_ME__.
# Generate secrets: openssl rand -hex 32   (JWT_SECRET, INTERNAL_SERVICE_TOKEN, DB/MinIO pw)
```

`MINIO_PUBLIC_ENDPOINT=storage.sanad.example.com` and `MINIO_PUBLIC_SECURE=true` make
presigned upload URLs sign for the TLS public host (uploads 403 otherwise).

## 3. Bring up the stack

```bash
docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml up -d --build
```

Caddy fetches TLS certs automatically. First boot pulls the embedding model (slow once).

Check: `curl -s https://sanad.example.com/api/... ` — the app is served by Caddy → web;
the API is reached server-side through the BFF. Health from the VM:
`docker compose -f infra/docker-compose.yml exec api curl -s localhost:8000/api/v1/health`.

## 4. Migrate + seed + create users

```bash
COMPOSE="docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml"
$COMPOSE run --rm migrate
$COMPOSE run --rm api python scripts/seed_regulations.py   # human-verified corpus
# Change the seeded demo password, or create real users, before go-live.
```

## 5. Research-agent egress sandbox (on the host, not in a container)

```bash
sudo AGENT_UPLINK=eth0 bash sandboxes/research-agent/netns/setup_agent_ns.sh
sudo systemctl enable --now agent-allowlist.timer   # refreshes the nftables allowlist every 60s
```

## 6. Go-live checklist

- [ ] All `__CHANGE_ME__` secrets replaced; `infra/.env` is `chmod 600`, never committed.
- [ ] Demo password rotated; real reviewer/admin users created.
- [ ] TLS valid on both domains; only 22/80/443 open.
- [ ] Corpus seeded and each article human-verified against the official gazette.
- [x] Backups scheduled: `sanad-backup.timer` runs `infra/deploy/backup.sh` nightly (Postgres dump + MinIO objects, 14-day rotation). Installed by `bootstrap.sh` step 5.
- [ ] `BACKUP_REMOTE` set in `infra/.env` (offsite rclone target) — local-only backups do not survive VM loss.
- [ ] Restore drill completed at least once (see below).
- [ ] MinIO server-side encryption confirmed on both buckets.

### Backup & restore

Backups land in `/var/backups/sanad` (`db-<ts>.sql.gz`, `minio-<ts>.tar.gz`). Verify the timer:

```bash
systemctl list-timers | grep sanad-backup
sudo /opt/sanad/infra/deploy/backup.sh   # run once on demand
```

Restore drill (do this once before go-live; use a scratch DB, do not overwrite prod):

```bash
# Postgres: restore the latest dump into a throwaway database and compare row counts.
gunzip -c /var/backups/sanad/db-<ts>.sql.gz \
  | docker compose exec -T postgres psql -U postgres -d postgres -c "CREATE DATABASE sanad_restore" -
gunzip -c /var/backups/sanad/db-<ts>.sql.gz \
  | docker compose exec -T postgres psql -U postgres -d sanad_restore
docker compose exec -T postgres psql -U postgres -d sanad_restore \
  -c "select count(*) from regulation_versions; select count(*) from findings; select count(*) from audit_log;"
# Compare against the same counts in the live `sanad` DB, then: DROP DATABASE sanad_restore;
```

## Wiring a real LLM later (no redeploy of app code)

Edit `infra/.env` and restart `api` + `worker`:
- Anthropic: `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY=…` (add `api.anthropic.com` to the
  agent allowlist; the key lives only in the analysis/agent service).
- Self-hosted (air-gapped): `LLM_PROVIDER=selfhosted`, `SELFHOSTED_LLM_URL=…` (OpenAI-compatible).

## Swapping in managed services (optional)

- **Postgres:** point `POSTGRES_*` at a managed instance that supports **pgvector** (RDS,
  Cloud SQL, Supabase). Run the role bootstrap SQL (`infra/postgres/init/00_roles.sh` logic)
  and `CREATE EXTENSION vector` once as an admin, then remove the `postgres` service.
- **Object storage:** point `MINIO_*` at S3/GCS (S3-compatible); drop the `minio` service and
  serve presigned URLs from the provider's endpoint.
- The two sandboxes still require a Linux VM you control — they cannot move to a managed PaaS.
