# database.md — SANAD data model

PostgreSQL 16 + pgvector. All tables have `id UUID PK DEFAULT gen_random_uuid()`, `created_at timestamptz DEFAULT now()`. Timestamps are UTC. Text is UTF-8/NFC. Arabic and English fields are separate columns (`*_ar`, `*_en`), never mixed.

## Core principle encoded in schema

Two invariants are enforced at the schema level, not just in code:
1. A `finding` cannot exist without a `regulation_version` citation (NOT NULL FK).
2. `regulation_versions` is append-only (no UPDATE/DELETE grant to the app role).

---

## users
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| email | text unique not null | |
| display_name | text not null | |
| role | text not null | enum: reviewer, sharia_board, admin, service |
| is_active | bool not null default true | |
| password_hash | text not null | bcrypt hash (architecture.md §7d); never returned by any API |
| created_at | timestamptz | |

## regulations
The regulatory bodies/frameworks. Reference data.
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| code | text unique not null | e.g. PDPL, ZATCA, SAMA, LABOR |
| name_ar | text not null | |
| name_en | text not null | |
| authority | text not null | issuing body |
| source_domain | text not null | e.g. sdaia.gov.sa |
| last_reconciled_at | timestamptz | when this regulation was last fetched/checked vs its source (staleness) |

## regulation_versions  (APPEND-ONLY, immutable evidence cache)
The heart of Zero Unsourced Findings. Never updated or deleted.
| column | type | notes |
|---|---|---|
| id | uuid PK | this is the `regulation_version_id` citations point to |
| regulation_id | uuid FK → regulations | |
| article_ref | text not null | e.g. "Article 29" |
| article_text_ar | text not null | full original text, verbatim |
| article_text_en | text | official/verified translation if available |
| source_url | text not null | where it was fetched |
| content_hash | text not null | sha256 of article_text_ar |
| fetched_at | timestamptz not null | |
| effective_date | date | when the article takes effect |
| supersedes_id | uuid FK → regulation_versions | previous version this replaces (null if first) |
| verified_by | uuid FK → users not null | who/what attested the text (a human, or the official-fetch service account) |
| verification_tier | text not null | `human_verified` \| `official_fetch` (CHECK). Default `human_verified`. Surfaced on citations so auto-fetched text is labeled. See AGENTS.md #5. |
| embedding | vector(1024) | pgvector, for retrieval |

Indexes: ivfflat on `embedding`; btree on `(regulation_id, article_ref)`.
DB grant: app role has INSERT + SELECT only. No UPDATE/DELETE.

## contracts
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| title | text not null | |
| uploaded_by | uuid FK → users | |
| raw_object_key | text not null | MinIO key, quarantine bucket |
| sanitized_object_key | text | MinIO key, set after Sandbox A |
| status | text not null | enum: uploaded, sanitizing, sanitized, extracting, reviewing, reviewed, failed |
| readiness_score | int | 0–100, nullable until computed; reviewed findings only |
| failure_reason | text | stable reason code when status=failed (architecture.md §7c); null otherwise |
| ocr_used | bool not null default false | the PDF had no text layer and was OCR'd (noisier text; surfaced as a badge) |
| created_at | timestamptz | |

## clauses
Segmented from sanitized contract text.
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| contract_id | uuid FK → contracts | |
| ordinal | int not null | position in contract |
| text_ar | text | |
| text_en | text | |
| embedding | vector(1024) | |

## findings
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| contract_id | uuid FK → contracts not null | |
| clause_id | uuid FK → clauses | nullable (contract-level findings) |
| regulation_version_id | uuid FK → regulation_versions **NOT NULL** | the citation gate, enforced in DB |
| title_ar | text not null | |
| title_en | text | |
| explanation_ar | text | generated strictly from cited article |
| explanation_en | text | |
| severity | text not null | enum: critical, high, medium, low |
| category | text not null | enum: regulatory, sharia |
| violation_cost_ar | text | fine range text from cited article |
| violation_cost_min | numeric | parsed min fine, nullable |
| violation_cost_max | numeric | parsed max fine, nullable |
| review_status | text not null default 'pending' | enum: pending, accepted, rejected |
| reviewed_by | uuid FK → users | set on review |
| reviewed_at | timestamptz | |

Rule: `readiness_score` and Radar/Kit consume only rows where `review_status <> 'pending'`.

## idea_checks  (PM feature)
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| submitted_by | uuid FK → users | |
| idea_text | text not null | PM's plain-language description (untrusted input) |
| report_ar | text | generated cited report |
| report_en | text | |
| status | text not null | enum: submitted, generated, reviewed |
| reviewed_by | uuid FK → users | compliance human gate |

## idea_check_citations
Join: an idea check's report references N regulation versions.
| column | type | notes |
|---|---|---|
| idea_check_id | uuid FK | |
| regulation_version_id | uuid FK → regulation_versions | |
| PK (idea_check_id, regulation_version_id) | | |

## obligations  (Register)
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| regulation_version_id | uuid FK → regulation_versions not null | source of the obligation |
| title_ar | text not null | |
| title_en | text | |
| owner_id | uuid FK → users | responsible person |
| due_date | date | |
| status | text not null | enum: open, in_progress, met, overdue |

## monitoring_events
Produced by the research agent + differ.
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| regulation_id | uuid FK → regulations | |
| new_version_id | uuid FK → regulation_versions | after human verification |
| change_type | text | enum: new_article, amended, repealed |
| detected_at | timestamptz | |
| impact_summary_ar | text | |
| status | text | enum: detected, verified, notified |

## audit_log  (append-only)
Every allow/deny/decision. Never mutated.
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| actor | text not null | user id, 'research-agent', or 'sanitizer' |
| action | text not null | e.g. agent_fetch, finding_reviewed, score_computed, egress_denied |
| target | text | contract id, domain, etc. |
| verdict | text | allowed / denied / n-a |
| detail_json | jsonb | domain, ip, rule matched, reason code |
| at | timestamptz not null default now() | |

DB grant: INSERT + SELECT only.

---

## invites
Single-use registration codes issued by an admin. A code carries the role the new account gets, and may be bound to a specific email.
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| code | text not null unique | `secrets.token_urlsafe(6)`; shared out-of-band |
| role | text not null | CHECK reviewer / sharia_board / admin |
| email | text | optional; if set, only that email may redeem it |
| note | text | free-text label for the admin |
| used | bool not null default false | flips true on successful register |
| used_by | uuid FK → users.id | who redeemed it |
| created_by | uuid FK → users.id | issuing admin |
| created_at | timestamptz not null default now() | |

DB grant: full CRUD (app marks codes used and lists them). Index on `code`.

---

## settings
Editable key/value app settings. Currently holds the admin-editable **analyst guidance** for the two analysis prompts (`contracts_guidance`, `idea_guidance`). Only the guidance/persona is stored here; the locked JSON+citation contract is appended in code and never editable, so a bad edit cannot break Zero Unsourced Findings.
| column | type | notes |
|---|---|---|
| key | text PK | e.g. `contracts_guidance`, `idea_guidance` |
| value | text not null | the guidance text |
| updated_by | uuid FK → users.id | last admin who saved |
| updated_at | timestamptz not null default now() | |

DB grant: full CRUD (admin upserts guidance).

---

## Relationship summary

```
regulations 1─* regulation_versions ─┬─* findings (NOT NULL citation)
                                      ├─* idea_check_citations
                                      ├─* obligations
                                      └─* monitoring_events
contracts 1─* clauses 1─* findings
users 1─* (uploads, reviews, verifications, ownership)
audit_log: standalone, append-only, references everything by id string
```

## Embeddings (decision)

`vector(1024)` matches **`intfloat/multilingual-e5-large`** (self-hosted, strong Arabic retrieval — see architecture.md §7b). Changing the embedding model to a different dimension is a MAJOR migration: new column, full re-embed job, index rebuild. Do not change casually.

## Indexes & constraints (complete list)

- `regulation_versions`: ivfflat (cosine) on `embedding`; btree `(regulation_id, article_ref)`; unique `(regulation_id, article_ref, content_hash)` — the same bytes are never stored twice for the same article.
- `clauses`: ivfflat (cosine) on `embedding`; btree `(contract_id, ordinal)`.
- `findings`: btree `(contract_id, review_status)`; btree `(regulation_version_id)`.
- `audit_log`: btree `(actor, at)`; btree `(action, at)`. BRIN on `at` if volume grows.
- All `status` / `severity` / `role` / `category` enums enforced as CHECK constraints (named, so migrations can evolve them explicitly).
- `contracts.updated_at timestamptz` maintained by trigger; all other tables rely on `created_at` + audit_log for history.
- App DB role grants: INSERT+SELECT only on `regulation_versions` and `audit_log`; full CRUD elsewhere. A separate `migrator` role owns DDL.
