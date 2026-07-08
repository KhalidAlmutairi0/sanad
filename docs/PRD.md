# SANAD (سَنَد) — Product Requirements Document

**Version:** 1.0 · **Owner:** Khalid Almutairi (personal project, NOT Entropy) · **Status:** Draft for build

---

## 1. One-line definition

SANAD is a sovereign AI compliance operating system for Saudi organizations. It catches the regulatory or Sharia violation in a contract — with its exact legal source — before signature, and continuously monitors the organization's regulatory posture against PDPL, ZATCA, SAMA, and Saudi Labor Law.

**Core promise: Zero Unsourced Findings.** Every finding is bound to the exact article text it cites, from a verified, versioned source. No source → no claim.

## 2. Problem

1. **Contract review is slow and expensive.** Legal/compliance review of a single commercial contract takes days to weeks and depends on scarce bilingual legal expertise.
2. **Regulations change faster than organizations can track.** SAMA circulars, NCA controls, PDPL implementing regulations, and ZATCA rules update continuously. Most organizations discover changes only when fined.
3. **Product teams build first, ask compliance later.** Features ship, then get blocked or reworked when compliance finds a violation — the most expensive possible time to find it.
4. **Generic AI tools hallucinate law.** LLMs invent article numbers and misquote regulations. In compliance, a confident wrong answer is worse than no answer.
5. **Data sovereignty blocks cloud tools.** Banks and government entities cannot send contracts to foreign-hosted AI services (SAMA/NCA requirements).

## 3. Target users

| Persona | Need | Primary tracks |
|---|---|---|
| Compliance officer (bank/fintech/enterprise) | Review contracts fast, defensibly, with audit trail | 1, 3 |
| Legal counsel | Negotiation-ready redlines with legal justification | 1 |
| Product manager | Know if an idea is compliant BEFORE building | Idea Check |
| Executive (CRO/CEO) | One number: "do we sign?" / "are we exposed?" | 1, 2 |
| Sharia board / Islamic bank | AAOIFI-aligned screening alongside regulatory screening | 5 |
| Fintech developer | Embed compliance checks into own product | 4 |

## 4. The five tracks (agreed priority order)

1. **Contract Review (reactive core).** Upload contract → extraction → clause-level analysis against PDPL, ZATCA, SAMA, Labor Law → findings with citations, severity, violation cost, and Contract Readiness Score. Human review gates everything.
2. **Continuous Regulatory Monitoring (proactive core).** Governed agent watches official regulator domains (sama.gov.sa, sdaia.gov.sa, zatca.gov.sa, hrsd.gov.sa, ncar/nca). New/changed legislation → impact analysis against org's contracts and obligations → alert owners before a violation exists.
3. **Regulatory Obligation Register.** The living backbone: every obligation the org carries, linked to source article, owning person, evidence documents, and deadlines. Fed by tracks 1 and 2.
4. **Embedded Compliance API.** The same engine exposed as an API for fintechs to embed (the ownership lever).
5. **Sharia Compliance Layer.** Parallel screening path aligned with AAOIFI standards and the client bank's own Sharia board precedents (the regional differentiator).

## 5. Feature set (v0.4 “Hackathon Edition” list, confirmed)

**Review layer**
1. **Zero Unsourced Findings** — every finding carries a resolvable citation to an immutable stored article version; findings without a verified source are structurally impossible (blocked at the pipeline gate, not by prompt discipline).
2. **Clause-level findings** — severity (critical/high/medium/low), category (regulatory/Sharia), status (pending/accepted/rejected by human reviewer).
3. **Violation Cost** — each finding displays the statutory fine range extracted from the violated article itself, cited.
4. **Contract Readiness Score** — one executive number per contract, computed ONLY from human-reviewed findings.
5. **Explain It (اشرح لي)** — one tap converts any legal finding into plain-language explanation, generated strictly from the cited article.
6. **Precedent Recall** — when a finding touches a structure the org's board/committee has ruled on before, SANAD surfaces the precedent inline, cited.
7. **Deal-breaker Radar** — 30-second pre-negotiation scan: GO / STOP / REVIEW with the 1–3 killer clauses cited.
8. **Negotiation Kit** — for every accepted high-severity finding: a redrafted clause + a short justification letter citing the regulation, exportable as a bilingual annex.

**PM layer**
9. **Idea Check (فحص الفكرة قبل البناء)** — a PM describes a feature idea in plain language; SANAD returns a cited compliance report in minutes: applicable regulations, requirements, risks, open questions. Human compliance officer reviews before it becomes the org's answer. Turns weeks of meetings into days. Reuses the exact same engine (retrieval, citations, gates — nothing architecturally new).

**Fetch layer**
10. **Governed Research Agent** — fetches official regulatory texts ONLY from allowlisted government domains, inside an egress-controlled sandbox, fully logged; nothing enters the citation store without human verification.

**Foundation**
11. **Sovereign deployment** — on-prem inside KSA, self-hosted model behind a swappable interface, bank-grade security (SAMA + NCA aligned), tenant isolation, encrypted MinIO storage, roles (Reviewer / Sharia Board / Admin / Service).
12. **Immutable evidence cache** — every cited article version is stored append-only; a citation made in January resolves to the same bytes in an audit in March.
13. **Full audit log** — every agent request (allowed or denied), every finding decision, every score computation is logged and queryable.

## 6. Security architecture requirement (from sandbox work, 2026-07-08)

Three mutually isolated environments — this is a hard requirement, not an implementation detail:

1. **Upload Sanitizer Sandbox** — processes user-uploaded files. NO network at all (`unshare-net` class isolation), read-only bind of the raw file, tmpfs scratch, strict timeout + cgroup limits, output = clean extracted text only. Prompt-injection text in uploads survives extraction by design; neutralization happens at the prompt layer (untrusted-data tagging), not here.
2. **Governed Research Agent Sandbox** — HAS network, but egress-restricted by a **dynamic allowlist** (nftables sets updated by a DNS watcher — static IPs proven to break within minutes on CDN-backed domains; validated empirically 2026-07-08). IPv6 explicitly disabled unless provisioned. Allowlist = official .gov.sa regulator domains + LLM API domain only. Every request logged.
3. **Analysis Environment** — consumes outputs of both, has no special privileges of its own, no direct file access, no unrestricted network.

Raw uploads NEVER enter the research agent's environment (exfiltration risk).

**Isolation boundary for the current build:** Linux namespaces + nftables (research agent) and bubblewrap (sanitizer) — validated working. This IS the production isolation for v1, not a placeholder. Firecracker microVMs are an OPTIONAL future hardening path (post-v1), NOT part of the current build. Do not block or scope any current work on Firecracker.

## 7. Non-functional requirements

- **Arabic-first, fully bilingual** (Arabic ⇄ English), RTL-correct everywhere. Stacked bilingual output in generated documents (full English block, then full Arabic block — never inline-mixed).
- **Latency:** contract review ≤ 10 min for 50-page contract; Idea Check ≤ 5 min; Deal-breaker Radar ≤ 30 s.
- **Auditability:** any finding reconstructable byte-for-byte 5+ years later.
- **Availability:** single-tenant on-prem; 99.5% within customer SLA.
- **Model swappability:** LLM behind one interface; Anthropic/OpenAI API or self-hosted model interchangeable per deployment.

## 8. MVP scope (build order)

1. Contract upload → sanitizer → extraction → findings with citations (PDPL + Labor Law first)
2. Human review workflow (accept/reject findings) → Contract Readiness Score
3. Immutable evidence cache + citation resolution
4. Idea Check (reuses 1–3)
5. Governed research agent (manual verification gate) feeding the cache
6. Violation Cost + Deal-breaker Radar + Negotiation Kit
7. Obligation Register + monitoring alerts
8. Sharia layer, Embedded API — post-MVP

## 9. Honest boundaries (stated in-product and in every pitch)

- NOT legal advice, NOT a fatwa — a cited starting map, always human-reviewed.
- NOT approval guarantee — regulators and Sharia boards decide.
- NOT a new risk surface: same grounding, same blocking, same gates across all features.

## 10. Open questions

- SNI-aware proxy vs nftables-set watcher for production egress control (watcher validated; proxy stronger for domain-level guarantees).
- Update cadence per regulator source; diffing strategy for amended articles.
- Sharia precedent ingestion format per client bank.
- CMA/SAMA positioning for the Embedded API track.
