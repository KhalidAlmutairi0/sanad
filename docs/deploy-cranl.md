# deploy-cranl.md — SANAD demo on CranL (DEPRECATED)

> DEPRECATED (2026-07-12). The fake-data demo mode this guide relied on has been removed
> (it fabricated findings/scores and violated AGENTS.md "no quick demo mode"). CranL also
> cannot run the isolation sandboxes. Do not use this path; deploy on a Linux VM per
> `docs/deploy.md`. Kept only for historical reference.

> DEMO deployment. CranL runs standard (unprivileged) containers, so the two isolation
> sandboxes do NOT run here: the upload sanitizer runs in `SANITIZER_MODE=direct` (no
> network containment) and the research agent is omitted. This drops SANAD's core security
> promise and is fine ONLY for a demo with non-sensitive files. For a real deployment use a
> Linux VM (`docs/deploy.md`), where the sandboxes work.

## Service → CranL mapping

CranL deploys one Dockerfile per **Application**, from a connected GitHub repo path.

| SANAD service | CranL resource | Build / config |
|---|---|---|
| web | Application | Dockerfile `apps/web/Dockerfile`, Port 3000, env `API_BASE_URL=<api app URL>` |
| api | Application | Dockerfile `apps/api/Dockerfile`, Port 8000, env `ROLE=api` + full env below |
| worker | Application | same Dockerfile `apps/api/Dockerfile`, env `ROLE=worker` (no port) |
| embedder | Application | Dockerfile `apps/embedder/Dockerfile`, Port 8081 (needs ~2 GB RAM for e5-large) |
| postgres+pgvector | **Managed Database** | must support the `vector` extension — see note |
| redis | **Managed Database** | for the arq queue |
| minio (object storage) | external S3 or a MinIO app | see note |

One image serves both `api` and `worker` via `ROLE` (see `apps/api/entrypoint.sh`).

## Required env (api + worker apps)

```
ROLE=api                      # worker app: ROLE=worker
APP_ENV=production
SANITIZER_MODE=direct         # DEMO: no-sandbox extraction (PaaS has no user namespaces)
LLM_PROVIDER=selfhosted       # offline stub for the demo

POSTGRES_HOST=... POSTGRES_PORT=5432 POSTGRES_DB=...
SANAD_APP_USER=... SANAD_APP_PASSWORD=...
SANAD_MIGRATOR_USER=... SANAD_MIGRATOR_PASSWORD=...
REDIS_HOST=... REDIS_PORT=6379
EMBEDDER_URL=<embedder app URL>
MINIO_ENDPOINT=<s3 host> MINIO_PUBLIC_ENDPOINT=<s3 host> MINIO_USE_SSL=true MINIO_PUBLIC_SECURE=true
MINIO_ROOT_USER=... MINIO_ROOT_PASSWORD=... MINIO_BUCKET_QUARANTINE=sanad-quarantine MINIO_BUCKET_SANITIZED=sanad-sanitized
JWT_SECRET=<openssl rand -hex 32>  INTERNAL_SERVICE_TOKEN=<openssl rand -hex 32>
```

web app env: `API_BASE_URL=https://<api-app-domain>` , `PORT=3000`.

## Deploy order

1. Create a **Project**; connect GitHub (`KhalidAlmutairi0/sanad`).
2. Create the **Databases**: Postgres (pgvector) + Redis. Create the app roles + `CREATE EXTENSION vector` once (the managed DB is a single superuser DB, so run the role bootstrap + extension manually via its console).
3. Create the **embedder** app; wait until healthy (model download).
4. Create the **api** app (`ROLE=api`); run migrations + seed once via a one-off command / job:
   `alembic upgrade head` then `python scripts/seed_regulations.py`.
5. Create the **worker** app (`ROLE=worker`).
6. Create the **web** app; set `API_BASE_URL` to the api app URL; add a custom domain + SSL.
7. Open the web domain, log in (`reviewer@sanad.local` / seeded password), upload a TXT/PDF/DOCX.

## Capability gaps to confirm on CranL (blockers if unmet)

1. **pgvector** on managed Postgres. If unsupported, point `POSTGRES_*` at an external
   pgvector-capable Postgres (Neon/Supabase) instead.
2. **Object storage**: CranL has no MinIO. Use an external S3-compatible bucket (set `MINIO_*`),
   or run MinIO as an app only if apps get a **persistent volume**.
3. **One-off commands / jobs** to run migrations + seed (or run them from a shell into the api app).

## Driving it from here

CranL exposes a REST API (`https://app.cranl.com/api`, Bearer `cranl_sk_…`) and an **MCP
server that supports Claude Code**. Connect the MCP (or provide a key) and I can create the
project, apps, and deployments via `cranl_create_app` / `cranl_deploy_app` directly.
