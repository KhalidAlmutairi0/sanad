# AGENTS.md — Instructions for coding agents working on SANAD

You are working on SANAD, a sovereign compliance platform for Saudi organizations. Read `plan.md` and `architecture.md` before touching code. These rules are non-negotiable invariants; if a task conflicts with them, stop and flag it instead of complying.

## Security invariants (never violate)

1. **Zero Unsourced Findings.** Any code path that creates a `finding` MUST require a valid `citation_id` referencing an existing row in `regulation_versions`. Enforce with a NOT NULL foreign key AND an application-layer gate. Never make citations optional "temporarily."
2. **Sandbox separation.** Three environments exist (see `architecture.md`): upload sanitizer (no network), research agent (allowlisted egress only), analysis (no special privileges). Never add network access to the sanitizer. Never mount customer files into the research agent environment. Never merge these environments "for convenience."
3. **Untrusted data tagging.** All extracted upload text and all fetched web content is UNTRUSTED. When passed to an LLM, wrap it in explicit untrusted-data delimiters and instruct the model to treat it as data, not instructions. Never interpolate untrusted text directly into system prompts.
4. **Evidence cache is append-only.** Never UPDATE or DELETE rows in `regulation_versions`. Corrections are new versions. Do not add admin endpoints that mutate stored article text.
5. **Human gates + verification tiers.** Every `regulation_versions` row carries a `verification_tier`: `human_verified` (a person reconciled the text against the official source) or `official_fetch` (parsed verbatim from the official gazette by the fetch tool, not yet human-reviewed — an explicit owner-policy trust of the official source, 2026-07-13). `official_fetch` rows are attributed to a distinct service account, never a human, and every citation to one is surfaced in the UI as auto-fetched/not-human-reviewed. Zero Unsourced Findings still holds (a finding still requires a resolvable citation); the tier records the *strength* of that source, it does not make citations optional. Scores compute only over findings with `review_status IN ('accepted','rejected')` — pending findings never affect scores.
6. **Audit everything.** Every agent fetch (allowed AND denied), every finding state change, every score computation writes to `audit_log`. Do not add code paths that skip it.
7. **Secrets.** No API keys in code, config files, or logs. Environment variables only. The LLM API key exists ONLY inside the research-agent/analysis service, never in the frontend or sanitizer.

## Bilingual rules

- Arabic-first UI, full RTL correctness. Use logical CSS properties (`margin-inline-start`, not `margin-left`).
- Generated documents (reports, annexes): stacked bilingual — full English block, then full Arabic block. NEVER mix English and Arabic inline on the same line.
- Font: IBM Plex Sans Arabic (see `style-guide.md`). No em dashes in Arabic or English output text.
- All user-facing strings go through the i18n layer (`ar` is the default locale, `en` secondary). No hardcoded strings in components.

## Stack & conventions

- **Frontend:** Next.js (App Router), TypeScript strict, Tailwind. Design tokens from `style-guide.md` only — no ad-hoc colors.
- **Backend:** FastAPI (Python 3.12+), Pydantic v2 models everywhere, async SQLAlchemy. Type hints mandatory.
- **DB:** PostgreSQL 16 + pgvector. Migrations via Alembic — never edit schema manually. Schema source of truth: `database.md`.
- **Storage:** MinIO (S3 API), server-side encryption, one bucket per tenant deployment.
- **LLM access:** through `services/llm/` interface ONLY (swappable provider). Never call provider SDKs directly from feature code.
- **API:** follow `api-contracts.md` exactly. Breaking a contract requires updating the doc in the same PR.

## Code quality

- Tests required for: citation gate, sanitizer isolation (network denial test), allowlist enforcement, score computation, audit log writes.
- Small PRs, one concern each. Update the relevant doc (`database.md`, `api-contracts.md`, `architecture.md`) in the same PR as the code change.
- Errors: never swallow. Sanitizer/agent failures must produce audit entries with reason codes.
- Arabic text handling: always UTF-8, normalize with NFC, never assume LTR in string manipulation or PDF generation.

## Definition of Done (every task)

A change is done ONLY when all of these hold:
1. Invariant tests still pass (citation gate, sanitizer no-network, allowlist denial, reviewed-only scoring, audit writes).
2. The relevant doc (`database.md` / `api-contracts.md` / `architecture.md`) is updated in the SAME commit if schema, endpoints, or flows changed.
3. Arabic AND English paths verified for any user-facing change (RTL layout, stacked bilingual output).
4. New failure paths emit audit entries with a stable reason code from `api-contracts.md` (e.g. `sanitize_timeout`, `egress_denied`) — no new ad-hoc codes without adding them to the doc.
5. No new dependency on provider SDKs outside `services/llm/`, no secrets in code, no localStorage for sensitive data.

## What NOT to build

- No feature that outputs legal conclusions without citations.
- No "quick demo mode" that bypasses human review gates.
- No telemetry or external calls from on-prem deployments except the configured LLM endpoint through the governed egress path.
- No browser localStorage for sensitive data.
