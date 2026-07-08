# architecture.md — SANAD system architecture

## 1. High-level view

```
                        ┌──────────────────────────────────────────────┐
                        │            Customer premises (KSA)           │
                        │                                              │
  User (browser) ──────▶│  Next.js Web ──▶ FastAPI (Analysis Env)      │
                        │                     │        │               │
                        │                     │        ▼               │
                        │                     │   PostgreSQL+pgvector  │
                        │                     │   MinIO (encrypted)    │
                        │                     │                        │
                        │        ┌────────────┴─────────────┐          │
                        │        ▼                          ▼          │
                        │  [Sandbox A]                [Sandbox B]      │
                        │  Upload Sanitizer           Research Agent   │
                        │  NO NETWORK                 ALLOWLISTED NET  │
                        │  raw file → clean text      gov sites + LLM  │
                        └──────────────────────────────────│───────────┘
                                                           ▼
                                     Internet: *.gov.sa regulators, LLM API only
```

## 2. The three isolated environments (hard boundary, validated 2026-07-08 PoC)

### Sandbox A — Upload Sanitizer
Threat: the uploaded file itself (malicious macro, parser exploit, zip bomb, embedded prompt injection, phone-home payload).

- **No network namespace at all** (`--unshare-net`): even successful code execution inside cannot reach anywhere. Verified: DNS resolution itself fails inside.
- Raw file bind-mounted **read-only** at a fixed path; everything else is tmpfs (RAM-backed, auto-wiped).
- `--unshare-pid`, `--die-with-parent`, strict `timeout`, cgroup memory/CPU caps (OOM-kill on abuse).
- Output contract: **plain text only** — no macros, scripts, embedded objects, or formatting survive.
- Prompt-injection strings in the text are NOT removed here (that is impossible to do reliably at this layer). They pass through and are neutralized at the prompt layer by untrusted-data tagging. This sandbox's job is containment, not content understanding.
- Implementation: bubblewrap. This is the production isolation for v1 (validated working). Firecracker is an optional post-v1 hardening path, not required now.

### Sandbox B — Governed Research Agent
Threat: an internet-connected agent is an exfiltration channel and an attack surface.

- Dedicated network namespace (`agent-ns` pattern): own interfaces, own nftables table, veth + NAT to host.
- **`policy drop` on output**: everything denied unless explicitly allowed.
- Allowed: loopback; established/related; DNS to the configured resolver; TCP 443 to `@allowed_ips`.
- **`@allowed_ips` is a dynamic nftables set**, refreshed every 60s by a DNS watcher (systemd timer) over `allowlist.yaml` domains. *Empirically required:* CDN-backed domains rotate IPs within minutes; static IP rules break silently (observed live against a Vercel-hosted domain during PoC).
- **IPv6 disabled at kernel level** inside the namespace (`disable_ipv6=1`). *Empirically required:* Happy Eyeballs caused Python clients to attempt IPv6 first and hang to timeout instead of failing over; explicit disable removes the silent failure class.
- Allowlist contents: official regulator domains (sama.gov.sa, sdaia.gov.sa, zatca.gov.sa, hrsd.gov.sa, …) + the LLM API domain. Nothing else, ever.
- The agent **never sees customer files or extracted contract text**. Its only job: fetch official regulatory texts, diff against stored versions, submit candidates to the human verification queue.
- Every request — allowed or denied — is written to `audit_log` with domain, IP, verdict, and rule matched.
- Known open decision: nftables-set watcher (validated) vs SNI-aware proxy (stronger name-level guarantee, immune to IP rotation). Documented as an open question; watcher ships first.

### Analysis Environment (FastAPI)
- No special privileges: no direct raw-file access, no unrestricted egress (host firewall allows DB, MinIO, queue, and the LLM endpoint via the governed path only).
- Consumes: sanitized text (from A, via MinIO+queue) and verified regulation versions (from B, via the evidence cache after human approval).
- Hosts the citation gate, scoring, retrieval, and LLM orchestration.

## 3. Data flow — Contract Review

1. Upload → MinIO (quarantine bucket) → job queued.
2. Sanitizer (A) pulls file read-only → clean text → MinIO (sanitized bucket). Audit entry.
3. Extraction segments clauses; retrieval (pgvector) finds candidate articles from `regulation_versions`.
4. LLM analyzes clause + retrieved articles (untrusted-data tagged) → draft findings.
5. **Citation gate**: any draft finding without a resolvable `regulation_versions` reference is rejected structurally. Audit entry.
6. Human reviewer accepts/rejects each finding.
7. Readiness Score computed from reviewed findings only. Violation Cost read from the cited article. Radar/Kit/Explain-It render from the same reviewed findings.

## 4. Data flow — Idea Check (PM feature)

Same engine, different input: PM's plain-language idea (treated as untrusted input, sanitized as text) → retrieval over the evidence cache → cited draft report (applicable regs, requirements, risks, open questions) → human compliance review → published answer. No new architecture.

## 5. Data flow — Monitoring

Timer → agent (B) fetches allowlisted regulator pages → differ detects changed articles → candidate version in verification queue → human verifies → new **append-only** row in `regulation_versions` → impact job matches affected obligations/contracts → alerts to owners.

## 6. Evidence cache (immutability)

- `regulation_versions` is append-only: no UPDATE/DELETE at DB-privilege level (revoked) and application level.
- Each row: full article text, source URL, fetch timestamp, content hash, verifier identity.
- A citation stores `regulation_version_id` — an audit in March resolves a January finding to identical bytes.

## 7. LLM layer

- Single interface `services/llm/` — provider-swappable per deployment: Anthropic/OpenAI API (through Sandbox-B-style governed egress) or fully self-hosted model (air-gapped option).
- System prompts are code-reviewed artifacts. Untrusted content is delimited and labeled; models are instructed to treat it as data.

## 7b. Embeddings (decision)

- **Model: `intfloat/multilingual-e5-large` (1024 dims), self-hosted.** Rationale: strong Arabic retrieval quality, runs on-prem (sovereignty — embedding legal text must not leave the deployment), and fixes `vector(1024)` in the schema as a real decision, not a placeholder.
- Served as a small internal service in the analysis environment; used for both `regulation_versions.embedding` and `clauses.embedding`. Swappable behind `services/retrieval/embedder.py`, but changing dimensions requires a migration + re-embed job — treat as a major change.

## 7c. Jobs & queue (decision)

- **Queue: Redis 7 + `arq`** (async Python worker library). Rationale: one lightweight extra container, native asyncio (matches FastAPI), simple on-prem story. No Kafka/RabbitMQ complexity for v1.
- Job types: `sanitize_contract`, `extract_clauses`, `generate_findings`, `generate_idea_report`, `agent_fetch_cycle`, `impact_analysis`, `compute_embeddings`.
- **Retry policy:** max 3 attempts, exponential backoff; on final failure the job writes an `audit_log` entry with a reason code and sets the owning entity's status to `failed` — never silently drops. Sanitizer jobs are NOT retried on timeout/OOM verdicts (a file that kills the sandbox is quarantined and flagged, not re-run).
- The sanitizer worker consumes jobs from Redis but executes the actual extraction inside the bwrap sandbox as a subprocess; the worker process itself stays outside the sandbox.

## 7d. AuthN/AuthZ

- JWT (short-lived access token, 8h) issued by the API on login; bcrypt password hashes. On-prem deployments may later swap in the customer's SSO (OIDC) behind the same session interface — designed for, not built in v1.
- Role checks (reviewer / sharia_board / admin / service) enforced as FastAPI dependencies per router; `service` role is for sandbox workers calling `/internal/*` endpoints with a deployment-local service token.

## 8. Deployment model

- **Self-hosted / on-prem per customer**: each entity runs its own full instance on its own infrastructure. No central multi-tenant platform.
- "Multi-tenant" inside a deployment means isolating multiple agents/workloads from each other, not multiple customers.
- Roles: Reviewer / Sharia Board / Admin / Service. Encrypted storage (MinIO SSE), TLS internal, SAMA+NCA-aligned controls checklist per install.

## 9. Optional future hardening (post-v1, NOT current scope)

The v1 isolation (namespaces + nftables + bubblewrap) is production-grade and complete on its own. IF stronger kernel-level boundaries are ever required by a specific customer's threat model, both sandboxes can later migrate to Firecracker microVMs behind the SAME contracts and data flows (no application changes). This is explicitly out of scope for the current build and must not block any v1 work.
