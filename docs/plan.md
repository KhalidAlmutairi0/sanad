# plan.md — SANAD Master Plan

## The problems SANAD solves, and how

| # | Problem | How SANAD solves it |
|---|---|---|
| 1 | Contract review takes weeks and scarce bilingual legal expertise | AI clause-level review against PDPL/ZATCA/SAMA/Labor Law, findings in minutes, human reviewer approves — weeks → days |
| 2 | Confident AI hallucination of law is worse than no answer | **Zero Unsourced Findings**: a finding cannot exist without a resolvable citation to an immutable stored article version — enforced by a pipeline gate, not prompt discipline |
| 3 | Regulations change silently; orgs find out via fines | Governed research agent watches official regulator domains on schedule; changes → impact analysis → alerts to obligation owners BEFORE violation |
| 4 | PMs build first, discover compliance blockers after | **Idea Check**: plain-language feature idea in → cited compliance report out in minutes (applicable regs, requirements, risks, open questions) → human-reviewed |
| 5 | Executives can't answer "do we sign?" quickly | Contract Readiness Score (one number, human-reviewed findings only) + Deal-breaker Radar (GO/STOP/REVIEW in 30s) |
| 6 | Finding problems ≠ fixing them | Negotiation Kit: redrafted clause + cited justification letter, bilingual annex export |
| 7 | Fines are abstract until they land | Violation Cost: statutory fine range shown per finding, from the violated article itself |
| 8 | Sovereignty: contracts can't leave KSA | Full on-prem deployment, swappable model interface, encrypted MinIO, SAMA/NCA-aligned controls |
| 9 | Malicious/booby-trapped uploads can attack the system | Upload Sanitizer Sandbox: no network, read-only input, tmpfs, timeout, cgroups — output is clean text only |
| 10 | An agent with internet access is an exfiltration channel | Research agent runs in an egress-controlled sandbox: dynamic nftables allowlist (gov domains + LLM API only), IPv6 disabled, everything logged; it never sees customer files |
| 11 | Auditors ask "why did you approve this in January?" | Immutable evidence cache + full audit log: every citation resolves to the same bytes years later |
| 12 | Islamic banks need Sharia + regulatory in one pass | Parallel Sharia screening layer (AAOIFI + client board precedents), same citation discipline |

## Phased plan

**Phase A — Reviewed core (MVP heart)**
Upload → sanitize → extract → findings (PDPL + Labor Law) → human review → Readiness Score. Evidence cache + citations live from day one. Exit: one real contract reviewed end-to-end with zero unsourced findings.

**Phase B — PM layer**
Idea Check on top of the same engine. Exit: PM question → cited report → human sign-off in < 1 day.

**Phase C — Fetch layer**
Governed research agent (sandboxed, allowlisted, logged) + human verification gate feeding the cache. Add ZATCA + SAMA corpora. Exit: a regulator page change lands in the cache as a new verified version with diff.

**Phase D — Monitoring + Register**
Obligation Register, change alerts, owner assignment, deadlines. Exit: a simulated regulation change produces a correct, cited alert to the right owner.

**Phase E — Negotiation & executive layer**
Violation Cost, Deal-breaker Radar, Precedent Recall, Negotiation Kit, Explain It.

**Phase F — Expansion**
Sharia layer, Embedded Compliance API. (Optional, post-v1: Firecracker hardening of both sandboxes — only if a customer threat model demands it. Not required for a strong v1.)

## What "done right" means (invariants)

1. No finding without a citation that resolves in the evidence cache. Ever.
2. Raw uploads never reach any environment that has network access.
3. Nothing enters the citation store without human verification.
4. Scores are computed only from human-reviewed findings.
5. Every allow/deny/decision is in the audit log.

## Success metrics (measurable)

- **Citation integrity:** 100% of findings resolve to a stored article version (structural — measured by a scheduled integrity job, target: zero violations ever).
- **Review speed:** 50-page contract, upload → all findings generated ≤ 10 min; reviewer completes triage ≤ 1 working day.
- **Idea Check turnaround:** submission → cited draft report ≤ 5 min; human-reviewed answer ≤ 1 working day.
- **Finding precision (human-judged):** ≥ 80% of generated findings accepted by reviewers by end of Phase A pilot; track acceptance rate per regulation over time.
- **Monitoring latency (Phase C+):** regulator page change → verified new version in cache ≤ 48h.
- **Audit completeness:** every state change has an audit row (verified by test + scheduled reconciliation).

## Top risks & mitigations

| Risk | Mitigation |
|---|---|
| LLM misreads Arabic legal text → wrong findings | Citation gate limits damage (claim must bind to real article); human review gate catches the rest; track per-regulation acceptance rate as an early-warning signal |
| Seed corpus quality (bad ingestion = bad everything) | Small, human-verified corpus first (PDPL + Labor Law); every seeded article carries verifier identity; expand only after Phase A proves the loop |
| Regulator sites change structure → agent/differ breaks | Differ failures alert, never silently pass; human verification gate means broken fetches cannot corrupt the cache |
| Allowlist drift (IP rotation) silently blocks the agent | DNS watcher on a 60s timer + denied-egress audit entries surface it immediately (validated failure mode) |
| Scope creep before the core loop works | Phases have exit criteria; nothing from a later phase starts before the earlier exit criterion is demonstrated |
| Single developer bandwidth | Vertical slice first (Phase A end-to-end) so the project is demonstrable at every stage |
