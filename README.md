# SANAD (سَنَد)

Sovereign AI compliance platform for Saudi organizations. Catches the regulatory or
Sharia violation in a contract — with its exact legal source — before signature.

Core promise: **Zero Unsourced Findings.** No source, no claim.

See `docs/` for the full plan, architecture, data model, API contracts, and design
system. `AGENTS.md` holds the non-negotiable security invariants.

## Quick start (local)

```bash
cp infra/.env.example infra/.env      # fill in ANTHROPIC_API_KEY if using the Anthropic provider
docker compose -f infra/docker-compose.yml up --build
```

Services:

| Service   | URL                     | Purpose                                  |
|-----------|-------------------------|------------------------------------------|
| web       | http://localhost:3000   | Next.js frontend (Arabic-first, RTL)     |
| api       | http://localhost:8000   | FastAPI analysis environment             |
| embedder  | http://localhost:8081   | multilingual-e5-large embedding service  |
| minio     | http://localhost:9001   | object storage console (quarantine/sanitized) |
| postgres  | localhost:5432          | PostgreSQL 16 + pgvector                 |
| redis     | localhost:6379          | arq job queue                            |

Health check: `curl http://localhost:8000/api/v1/health`

## Detailed run instructions

Filled in as deliverables land — see the bottom of this file.

## Repository layout

`apps/web`, `apps/api`, `sandboxes/sanitizer`, `sandboxes/research-agent`, `infra/`,
`scripts/`. Full tree in `docs/project-structure.md`.
