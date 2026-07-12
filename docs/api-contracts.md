# api-contracts.md — SANAD API

Base: `/api/v1`. Auth: Bearer JWT. All responses JSON. Errors: `{ "error": { "code": string, "message_ar": string, "message_en": string } }`. Bilingual text fields are separate (`*_ar` / `*_en`), never inline-mixed. Timestamps ISO 8601 UTC.

**Pagination (all list endpoints):** query `?limit=` (default 25, max 100) and `?offset=` (default 0); responses include `"total": int`. 

**Error codes (stable, used in `error.code`):** `unauthorized`, `forbidden`, `not_found`, `validation_failed`, `citation_required` (attempt to create a finding without a source — should never occur, logged as an incident), `sanitize_failed`, `sanitize_timeout`, `file_too_large`, `unsupported_file_type`, `egress_denied`, `review_conflict`, `rate_limited` (429; too many auth attempts from one IP).

**Upload constraints:** accepted types pdf, docx, txt; max 50 MB; anything else → 422 `unsupported_file_type` / 413 `file_too_large` before touching the sanitizer.

### GET /health
No auth. Res 200: `{ "status": "ok", "db": true, "storage": true, "queue": true }` — used by compose healthchecks and on-prem monitoring.

Breaking any contract here requires updating this doc in the same PR.

---

## Auth

### POST /auth/login
Req: `{ "email": string, "password": string }`
Res 200: `{ "token": string, "user": { "id", "display_name", "role" } }`
Rate limit: 5 requests/minute per client IP (X-Forwarded-For behind the proxy); the 6th returns 429 `rate_limited`.

### POST /auth/register
Public. Redeem a single-use invite code to create an account, then auto-login.
Req: `{ "email": string, "password": string, "code": string, "display_name"?: string }`
Res 201: `{ "token": string, "user": { "id", "display_name", "role" } }`
Errors: `validation_failed` if the code is unknown/used, bound to another email, the email already exists, or the password is shorter than 6 chars. Role is taken from the invite, never from the request. Marks the invite used and writes `user_registered` to the audit log.

---

## Contracts

### POST /contracts
Create + get upload target. Req: `{ "title": string }`
Res 201: `{ "id": uuid, "upload_url": string }`  (presigned MinIO PUT, quarantine bucket)

### POST /contracts/{id}/uploaded
Signal upload complete → triggers sanitizer pipeline.
Res 202: `{ "id": uuid, "status": "sanitizing" }`

### GET /contracts
Res 200: `{ "items": [ { "id","title","status","readiness_score","created_at" } ], "total": int }`

### GET /contracts/{id}
Res 200:
```json
{
  "id": "uuid",
  "title": "string",
  "status": "reviewed",
  "readiness_score": 72,
  "findings_summary": { "critical": 1, "high": 3, "medium": 5, "low": 2, "pending": 0 }
}
```

### GET /contracts/{id}/clauses
Res 200: `{ "items": [ { "id","ordinal","text_ar","text_en" } ] }`

---

## Findings

### GET /contracts/{id}/findings
Query: `?status=pending|accepted|rejected&severity=critical|high|medium|low`
Res 200:
```json
{
  "items": [
    {
      "id": "uuid",
      "clause_id": "uuid|null",
      "title_ar": "string", "title_en": "string",
      "explanation_ar": "string", "explanation_en": "string",
      "severity": "critical",
      "category": "regulatory",
      "violation_cost_ar": "string",
      "violation_cost_min": 10000, "violation_cost_max": 5000000,
      "review_status": "pending",
      "citation": {
        "regulation_version_id": "uuid",
        "regulation_code": "PDPL",
        "article_ref": "Article 29",
        "article_text_ar": "string",
        "source_url": "string",
        "effective_date": "2023-09-14"
      }
    }
  ]
}
```
Note: `citation` is never null. A finding without a resolvable citation cannot be returned (it cannot exist — DB NOT NULL).

### POST /findings/{id}/review
Req: `{ "decision": "accepted" | "rejected" }`
Res 200: `{ "id": uuid, "review_status": "accepted", "reviewed_at": "ts" }`
Side effects: recomputes contract `readiness_score` (reviewed findings only); writes `audit_log`.

### GET /findings/{id}/explain
"Explain It" — plain-language, generated strictly from cited article.
Res 200: `{ "explanation_ar": string, "explanation_en": string, "citation": { ... } }`

---

## Deal-breaker Radar

### GET /contracts/{id}/radar
Res 200:
```json
{
  "verdict": "STOP",
  "killers": [
    { "finding_id": "uuid", "title_ar": "...", "severity": "critical", "citation": { "...": "..." } }
  ]
}
```
`verdict` ∈ GO | REVIEW | STOP. `killers` length 0–3.

---

## Negotiation Kit

### GET /findings/{id}/kit
Only for accepted high/critical findings.
Res 200:
```json
{
  "redrafted_clause_ar": "string", "redrafted_clause_en": "string",
  "justification_letter_ar": "string", "justification_letter_en": "string",
  "citation": { "...": "..." }
}
```

### POST /findings/{id}/kit/export
Req: `{ "format": "docx" | "pdf" }`
Res 200: `{ "download_url": string }`  (stacked bilingual annex)

---

## Idea Check (PM feature)

### POST /idea-checks
Req: `{ "idea_text": string }`  (treated as untrusted input)
Res 202: `{ "id": uuid, "status": "submitted" }`

### GET /idea-checks
Paginated list of the deployment's idea checks (PM feature index page).
Res 200: `{ "items": [ { "id", "status" } ], "total": int }`

### GET /idea-checks/{id}
Res 200:
```json
{
  "id": "uuid",
  "idea_text": "string",
  "status": "generated",
  "report_ar": "string", "report_en": "string",
  "citations": [ { "regulation_version_id","regulation_code","article_ref","source_url" } ],
  "reviewed_by": "uuid|null"
}
```
Report sections: applicable regulations, requirements, risks, open questions — every claim carries a citation.

### POST /idea-checks/{id}/review
Req: `{ "decision": "reviewed", "notes_ar"?: string }`
Res 200: `{ "id": uuid, "status": "reviewed" }`

---

## Obligation Register

### GET /obligations
Query: `?status=open|in_progress|met|overdue&owner_id=uuid`
Res 200: `{ "items": [ { "id","title_ar","title_en","owner_id","due_date","status","citation":{...} } ] }`

### POST /obligations/{id}/assign
Req: `{ "owner_id": uuid, "due_date": "date" }`
Res 200: `{ "id": uuid, "owner_id": uuid, "due_date": "date" }`

---

## Monitoring

### GET /monitoring/events
Res 200:
```json
{ "items": [ { "id","regulation_code","change_type","detected_at","impact_summary_ar","status","new_version_id" } ] }
```

### POST /monitoring/events/{id}/verify
Human gate: promotes a detected change into the evidence cache.
Req: `{ "regulation_version": { "article_ref","article_text_ar","article_text_en"?,"source_url","effective_date" } }`
Res 201: `{ "regulation_version_id": uuid, "status": "verified" }`
Side effect: append-only insert into `regulation_versions` with `verified_by = caller`.

---

## Evidence cache (read-only)

### GET /evidence/versions/{regulation_version_id}
Res 200: full stored article (text_ar, text_en, source_url, content_hash, fetched_at, effective_date, verified_by, supersedes_id).

### GET /evidence/search
Query: `?q=string&regulation_code=PDPL`  (semantic search via pgvector)
Res 200: `{ "items": [ { "regulation_version_id","regulation_code","article_ref","snippet_ar","score" } ] }`

---

## Admin — agent allowlist & audit

### GET /admin/allowlist
Res 200: `{ "domains": ["sama.gov.sa","sdaia.gov.sa","zatca.gov.sa","hrsd.gov.sa","laws.boe.gov.sa"] }`
Regulator domains only. The LLM API host is deliberately NOT in this list; model egress uses its own governed path, never the research-agent regulator allowlist.

### PUT /admin/allowlist
Req: `{ "domains": [string] }`  (change triggers watcher refresh; audit-logged)
Res 200: `{ "domains": [string] }`

### GET /admin/audit
Query: `?actor=&action=&verdict=&from=&to=`
Res 200: `{ "items": [ { "actor","action","target","verdict","detail_json","at" } ], "total": int }`

### GET /admin/prompts
Admin only. Returns the editable analyst guidance for both analyses plus the read-only locked contract that is always appended.
Res 200: `{ "contracts_guidance": string, "idea_guidance": string, "contracts_contract": string, "idea_contract": string }`

### POST /admin/prompts
Admin only. Updates the editable guidance for both analyses (persona/intent only; the JSON+citation contract is fixed in code and cannot be changed). Empty guidance is rejected. Takes effect on the next analysis run. Audited as `prompts_updated`.
Req: `{ "contracts_guidance": string, "idea_guidance": string }`
Res 200: same shape as GET.

### POST /admin/invites
Admin only. Issue a single-use invite code. Req: `{ "role": "reviewer"|"sharia_board"|"admin", "email"?: string, "note"?: string }`
Res 201: `{ "code","role","email","used","created_at" }`  (audit: `invite_created`)

### GET /admin/invites
Admin only. Res 200: `{ "items": [ { "code","role","email","used","created_at" } ] }`

---

## Internal (service-to-service, not public)

- `POST /internal/sanitize-complete` — sanitizer → api: `{ "contract_id", "sanitized_object_key", "status" }`
- `POST /internal/agent-candidate` — research agent → api: submits a fetched article candidate to the verification queue. Never writes to `regulation_versions` directly; always goes through the human `verify` gate above.
