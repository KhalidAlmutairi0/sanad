# SANAD (سَنَد)

Sovereign AI compliance platform for Saudi organizations. SANAD catches the regulatory or
Sharia violation in a contract, with its exact legal source, before signature, and answers
"is this feature idea compliant?" for product teams.

**Core promise: Zero Unsourced Findings.** Every finding is bound to the exact article it
cites, from a verified, immutable, versioned source. No source, no claim.

See `docs/` for the full plan, architecture, data model, API contracts, and design system.
`AGENTS.md` holds the non-negotiable security invariants.

## What Phase A delivers

A working vertical slice, all local via Docker:

upload a contract → sanitize it in a no-network sandbox → segment clauses → retrieve
candidate articles from the evidence cache → generate findings (each with a resolvable
citation) → human reviewer accepts/rejects → Contract Readiness Score. Plus the PM **Idea
Check** on the same engine, and the reproduced research-agent egress sandbox.

## The three isolated environments

1. **Upload Sanitizer (Sandbox A)** — bubblewrap, `--unshare-net` (no network at all),
   read-only input, tmpfs, timeout, rlimits. Output is clean text only. `sandboxes/sanitizer/`.
2. **Research Agent (Sandbox B)** — network namespace + nftables `policy drop` + a dynamic
   allowlist set refreshed every 60s by a DNS watcher, IPv6 disabled. Never sees customer
   files. `sandboxes/research-agent/`.
3. **Analysis (FastAPI)** — no special privileges; consumes A's sanitized text and B's
   human-verified regulations. `apps/api/`.

## Prerequisites

- Docker + Docker Compose.
- The two sandboxes are **Linux-only** and need unprivileged user namespaces (Sandbox A)
  and root + nftables + `ip netns` (Sandbox B). On a Linux host they run for real; on
  Docker Desktop / macOS the isolation tests **skip** rather than fail.

## Quick start

```bash
cp infra/.env.example infra/.env
# Edit infra/.env: set strong passwords + JWT_SECRET (openssl rand -hex 32).
# Default LLM_PROVIDER=selfhosted runs a deterministic offline stub — no API key needed.
# To use Anthropic: set LLM_PROVIDER=anthropic and ANTHROPIC_API_KEY.

docker compose -f infra/docker-compose.yml up --build
```

First boot pulls the embedding model (multilingual-e5-large); the `embedder` service is
slow on cold start (a few minutes) and has a long healthcheck start period.

Then seed the evidence cache (small, real, human-verified PDPL + Labor Law corpus):

```bash
docker compose -f infra/docker-compose.yml run --rm api python scripts/seed_regulations.py
```

Open http://localhost:3000 and sign in:

| Email                  | Password             | Role     |
|------------------------|----------------------|----------|
| `reviewer@sanad.local` | `sanad-dev-password` | reviewer |
| `verifier@sanad.local` | `sanad-dev-password` | admin    |

(Override the seed password with `SEED_DEFAULT_PASSWORD`.)

### Services

| Service   | URL                     | Purpose                                   |
|-----------|-------------------------|-------------------------------------------|
| web       | http://localhost:3000   | Next.js frontend (Arabic-first, RTL)      |
| api       | http://localhost:8000   | FastAPI analysis environment              |
| api docs  | http://localhost:8000/api/v1/docs | OpenAPI                          |
| embedder  | http://localhost:8081   | multilingual-e5-large embedding service   |
| minio     | http://localhost:9001   | object storage console                    |

Health: `curl http://localhost:8000/api/v1/health`

## Verifying the slice end to end

1. Sign in as the reviewer. On **Contracts**, upload a PDF/DOCX/TXT contract.
2. Status moves uploaded → sanitizing → extracting → reviewing (poll the list / refresh).
   The sanitizer runs in the no-network sandbox; clauses are segmented and embedded.
3. Open the contract: the two-pane workspace shows the contract text and the findings.
   Every finding carries an orange **citation chip** — click it to see the exact stored
   article text, source URL, and effective date. A finding without a chip is impossible.
4. Accept/Reject findings. The **Readiness Score** dial recomputes over reviewed findings
   only; the Deal-breaker Radar shows GO / REVIEW / STOP.
5. **Idea Check** (`/idea-check`): submit a plain-language feature idea, get a cited
   compliance report on the same engine.

## Tests (the invariants)

```bash
# API invariant + unit tests (citation gate, reviewed-only scoring, audit + append-only,
# untrusted tagging, segmentation, violation cost). Needs the DB up.
docker compose -f infra/docker-compose.yml run --rm api pytest -v

# Sanitizer no-network proof (Sandbox A). Linux + user namespaces required, else skips.
docker compose -f infra/docker-compose.yml run --rm api python -m pytest /sandboxes/sanitizer/tests -v

# Research-agent egress-denied proof (Sandbox B). Run on a Linux host as root:
sudo python3 -m pytest sandboxes/research-agent/tests/test_egress_denied.py -v

# Frontend E2E + accessibility (Playwright) against a running stack:
cd apps/web && npm run e2e:install && BASE_URL=http://localhost:3000 npm run e2e

# Load / latency (k6) against a running, seeded stack:
k6 run -e BASE_URL=http://localhost:8000 -e EMAIL=reviewer@sanad.local \
       -e PASSWORD=sanad-dev-password infra/load/api_load.js

# Golden-set regression (real retrieval + citation engine; needs seed + embedder):
docker compose -f infra/docker-compose.yml run --rm -e RUN_GOLDEN=1 api pytest tests/test_golden_set.py -v
```

CI (`.github/workflows/ci.yml`) runs, on every PR: the static invariant greps, backend
pytest with an invariant-module coverage gate, frontend typecheck + build (+ public
Playwright specs), the Linux sandbox isolation suites, and dependency/image scans
(pip-audit, npm audit, Trivy). The full test methodology is in `docs/test-plan.md`.

### Invariant → how it is enforced → test

| Invariant | Enforcement | Test |
|---|---|---|
| Zero Unsourced Findings | DB NOT NULL FK `findings.regulation_version_id` + application citation gate | `tests/test_citation_gate.py` |
| Evidence cache append-only | app DB role has INSERT+SELECT only on `regulation_versions` / `audit_log` | `tests/test_audit_writes.py` |
| Score over reviewed findings only | scoring query filters `review_status IN ('accepted','rejected')` | `tests/test_score_reviewed_only.py` |
| Sanitizer has no egress | bwrap `--unshare-net` | `sandboxes/sanitizer/tests/test_no_network.py` |
| Agent egress allowlisted | netns + nftables policy drop + dynamic set | `sandboxes/research-agent/tests/test_egress_denied.py` |
| Untrusted data is tagged, never trusted | `services/llm` wraps all untrusted blocks; feature code cannot bypass | `tests/test_untrusted_tagging.py` |
| Audit everything | `services/audit` is a required dependency of every state change | `tests/test_audit_writes.py` |

## Notes & limitations

- **LLM providers:** `services/llm/` is the only LLM entry point (grep finds no provider
  SDK imports elsewhere). Default `selfhosted` runs a deterministic offline stub so the
  slice and tests work with no external model; every downstream invariant still runs. Set
  `LLM_PROVIDER=anthropic` (+ key) or point `SELFHOSTED_LLM_URL` at an on-prem model.
- **Seed corpus:** small and real, but each article must be reconciled against the official
  gazette by a human verifier before production (see `scripts/seed_data/regulations.yaml`).
- **Production cgroups:** the sanitizer uses rlimits + timeout locally; wrap it in
  `systemd-run --scope -p MemoryMax=… -p CPUQuota=…` for true cgroup caps on servers.
- **Firecracker is out of scope** for v1. Namespaces + nftables + bubblewrap is the
  production isolation.

## Repository layout

`apps/web`, `apps/api`, `apps/embedder`, `sandboxes/sanitizer`,
`sandboxes/research-agent`, `infra/`, `scripts/`. Full tree in `docs/project-structure.md`.
