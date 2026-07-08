# SANAD — Claude Code Build Prompt

Copy everything below the line into Claude Code, in an empty project folder, with the 8 SANAD `.md` files (PRD, plan, AGENTS, architecture, project-structure, style-guide, database, api-contracts) placed in a `docs/` subfolder (put AGENTS.md at the repo root).

---

You are building SANAD, a sovereign AI compliance platform for Saudi organizations. This is a serious, production-oriented project — build it strong, not as a throwaway demo.

## Before you write any code

1. Read ALL of these fully, in order: `AGENTS.md` (repo root), then `docs/plan.md`, `docs/architecture.md`, `docs/database.md`, `docs/api-contracts.md`, `docs/project-structure.md`, `docs/style-guide.md`, `docs/PRD.md`.
2. `AGENTS.md` contains non-negotiable invariants. If any instruction I give conflicts with them, stop and tell me — do not silently comply.
3. Confirm your understanding back to me in 8–10 lines: the three isolated environments, the Zero-Unsourced-Findings citation gate, the append-only evidence cache, and the human review gates. Then propose your build order for Phase A and wait for my "go" before coding.

## What to build: Phase A (MVP, end-to-end)

A working vertical slice: upload a contract → sanitize it in an isolated sandbox → extract clauses → generate findings against PDPL + Saudi Labor Law, each with a resolvable citation → human reviewer accepts/rejects → Contract Readiness Score. Plus the PM Idea Check on the same engine.

Everything must run locally with `docker compose up`.

### Stack (from the docs, do not substitute)
- Frontend: Next.js (App Router) + TypeScript strict + Tailwind. Arabic-first, RTL-correct, IBM Plex Sans Arabic. Design tokens ONLY from `docs/style-guide.md`.
- Backend: FastAPI (Python 3.12+), Pydantic v2, async SQLAlchemy, Alembic.
- DB: PostgreSQL 16 + pgvector. Schema exactly as `docs/database.md`.
- Storage: MinIO (S3), server-side encryption, quarantine + sanitized buckets.
- LLM: behind a single swappable interface `services/llm/` — implement an Anthropic provider AND a stub/self-hosted provider. No provider SDK imports anywhere else.
- Sanitizer sandbox: bubblewrap wrapper, `--unshare-net`, read-only input bind, tmpfs, timeout, cgroup caps. Include a test that PROVES no network egress is possible from inside it.
- Research agent sandbox: network namespace + nftables `policy drop` + dynamic allowlist set refreshed by a DNS watcher (systemd timer), IPv6 disabled in the namespace. Include a test that proves a non-allowlisted domain is denied. (This is validated design — I built the PoC by hand; reproduce it as scripts under `sandboxes/research-agent/netns/`.)

### Hard invariants to enforce in code (from AGENTS.md)
- A `finding` row CANNOT exist without a NOT NULL `regulation_version_id` FK. Enforce in DB schema AND an application gate. Write a test that a finding without a citation is rejected.
- `regulation_versions` and `audit_log` are append-only: grant the app DB role INSERT + SELECT only, no UPDATE/DELETE. Corrections are new versions.
- Readiness Score and Deal-breaker Radar compute ONLY over findings with `review_status IN ('accepted','rejected')`. Test this.
- All uploaded text and all fetched web content is UNTRUSTED: wrap in explicit untrusted-data delimiters before any LLM call; never interpolate into system prompts. The sanitizer does NOT try to strip injection strings — containment only.
- The research agent NEVER receives customer files or contract text.
- Every agent fetch (allowed and denied), every finding decision, every score computation writes to `audit_log`.
- No secrets in code/config/logs — env vars only. LLM API key lives only in the analysis/agent service.

### Bilingual rules
- Arabic default locale, English secondary, all strings through i18n (no hardcoded UI strings).
- Generated documents/reports: stacked bilingual — full Arabic block then full English block, each in its own `dir`. Never mix scripts on one line.
- No em dashes in any product copy. Use logical CSS properties only (`margin-inline-start`, never `left`).

### Phase A deliverables (build in this order)
1. Repo scaffold per `docs/project-structure.md` + `docker compose up` bringing up postgres+pgvector, minio, api, web.
2. Alembic migration creating every table in `docs/database.md` with the append-only grants and the NOT NULL citation FK.
3. `scripts/seed_regulations.py`: load a small, real, human-verified set of PDPL + Labor Law articles into `regulation_versions` (with embeddings). Keep it small but real.
4. Sanitizer sandbox + its no-network test. Wire upload → sanitize → sanitized text in MinIO.
5. Extraction (clause segmentation) + retrieval (pgvector) + LLM finding generation through `services/llm/`, passing the citation gate. Findings API per `docs/api-contracts.md`.
6. Review workflow endpoints + Readiness Score (reviewed-only) + audit writes.
7. Frontend: login, contracts list, upload, and the two-pane review workspace (contract | findings) with the citation chip popover (the signature element), severity badges, and the Readiness Score dial — all per `docs/style-guide.md`, light theme default + dark theme.
8. Idea Check: submit endpoint + report generation (same engine) + a simple PM page.
9. Tests for every invariant above. A short `README.md` with run instructions.

### Working style
- Small, focused commits; update the relevant doc in `docs/` in the same commit as any schema or API change.
- After each numbered deliverable, pause and show me what you did and how to verify it before moving on.
- If something in the docs is ambiguous or you hit a real trade-off, ask me rather than guessing.
- Do NOT build Firecracker anything. The namespaces + nftables + bubblewrap isolation is the production isolation for v1. Firecracker is explicitly out of scope.

Start by reading the docs and giving me your confirmation + proposed Phase A order. Then wait for my go.
