# project-structure.md — SANAD repository layout

Monorepo. Two deployable apps (web, api), two sandboxed workers (sanitizer, research-agent), shared infra.

```
sanad/
├── docs/
│   ├── PRD.md
│   ├── plan.md
│   ├── architecture.md
│   ├── database.md
│   ├── api-contracts.md
│   └── style-guide.md
├── AGENTS.md
│
├── apps/
│   ├── web/                          # Next.js (App Router) frontend
│   │   ├── app/
│   │   │   ├── (auth)/login/
│   │   │   ├── contracts/            # list, upload, review workspace
│   │   │   │   └── [id]/
│   │   │   │       ├── findings/
│   │   │   │       ├── radar/        # Deal-breaker Radar view
│   │   │   │       └── kit/          # Negotiation Kit export
│   │   │   ├── idea-check/           # PM feature: submit idea, view report
│   │   │   ├── register/             # Obligation Register
│   │   │   ├── monitoring/           # regulation change feed + alerts
│   │   │   ├── evidence/             # browse evidence cache (read-only)
│   │   │   ├── admin/                # users, roles, allowlist review queue
│   │   │   └── api/                  # route handlers (BFF only, no logic)
│   │   ├── components/
│   │   │   ├── ui/                   # design-system primitives (tokens only)
│   │   │   ├── findings/             # FindingCard, CitationPopover, SeverityBadge
│   │   │   ├── score/                # ReadinessScore dial
│   │   │   └── bilingual/            # StackedBilingual, RTLProvider
│   │   ├── lib/                      # api client, i18n, auth
│   │   ├── locales/
│   │   │   ├── ar/                   # default
│   │   │   └── en/
│   │   └── tailwind.config.ts        # tokens imported from style-guide
│   │
│   └── api/                          # FastAPI backend (analysis environment)
│       ├── app/
│       │   ├── main.py
│       │   ├── core/                 # config, security, deps
│       │   ├── models/               # SQLAlchemy models (mirror database.md)
│       │   ├── schemas/              # Pydantic v2 request/response schemas
│       │   ├── routers/
│       │   │   ├── contracts.py
│       │   │   ├── findings.py
│       │   │   ├── idea_checks.py
│       │   │   ├── register.py
│       │   │   ├── monitoring.py
│       │   │   ├── evidence.py
│       │   │   └── admin.py
│       │   ├── services/
│       │   │   ├── llm/              # provider-swappable interface (ONLY LLM entry)
│       │   │   │   ├── base.py
│       │   │   │   ├── anthropic_provider.py
│       │   │   │   └── selfhosted_provider.py
│       │   │   ├── citations/        # citation gate — findings blocked without source
│       │   │   ├── scoring/          # Readiness Score (reviewed findings only)
│       │   │   ├── extraction/       # clause segmentation over sanitized text
│       │   │   ├── retrieval/        # pgvector search + embedder.py (multilingual-e5-large client)
│       │   │   └── audit/            # audit_log writer (mandatory dependency)
│       │   └── workers/              # arq (Redis) job consumers: sanitize, extract, findings, idea reports
│       ├── alembic/                  # migrations
│       └── tests/
│           ├── test_citation_gate.py
│           ├── test_score_reviewed_only.py
│           └── test_audit_writes.py
│
├── sandboxes/
│   ├── sanitizer/                    # Upload Sanitizer (NO network)
│   │   ├── run_sanitizer.sh          # bwrap wrapper: --unshare-net, ro-bind, tmpfs, timeout
│   │   ├── extract.py                # pdf/docx/txt → clean text (no macros, no scripts)
│   │   └── tests/test_no_network.py  # proves egress is impossible
│   │
│   └── research-agent/               # Governed Research Agent (allowlisted egress)
│       ├── netns/
│       │   ├── setup_agent_ns.sh     # namespace + veth + NAT + nftables (policy drop)
│       │   ├── update_allowlist.sh   # DNS watcher → nftables set refresh
│       │   └── agent-allowlist.timer # systemd timer (60s)
│       ├── agent/
│       │   ├── fetcher.py            # fetch from allowlisted regulator domains
│       │   ├── differ.py             # article change detection
│       │   └── submit_for_review.py  # → verification queue (human gate)
│       ├── allowlist.yaml            # sama.gov.sa, sdaia.gov.sa, zatca.gov.sa, hrsd.gov.sa, LLM API
│       └── tests/test_egress_denied.py
│
├── infra/
│   ├── docker-compose.yml            # postgres+pgvector, redis (arq queue), minio, api, web, workers, embedder
│   ├── .env.example                  # every env var documented; no real secrets ever committed
│   └── deploy/                       # on-prem install scripts per customer
│
└── scripts/
    ├── seed_regulations.py           # initial PDPL/Labor Law corpus load (human-verified)
    └── demo_contract.py
```

## Rules encoded by this layout

- `sandboxes/` never imports from `apps/` and vice versa — communication is via queue + object storage only.
- `services/llm/` is the single LLM gateway; grep for provider SDK imports outside it should return nothing.
- `services/audit/` is a required dependency of every state-changing service.
- Docs live with code; changing a contract or schema without updating its doc fails review.
