# SANAD Regulatory Monitoring — Status

Continuous-monitoring track. Fetching is now **per-source adapters** (Saudi regulator sites
differ in DOM, PDF-vs-HTML, and Arabic encoding), sitting on top of the existing source-agnostic
machinery: content-hash change detection, article-level chunking, pgvector storage with
metadata, retrieval + citation gate, and the two-stage human verify gate.

**Scheduling is intentionally manual** — the check runs on demand via `POST /monitoring/run-check`
(reviewer/admin). No cron/scheduler is wired. `run-check` is free (fetch + text diff, zero
tokens); turning a detected change into a `monitoring_event` is a separate, explicit,
token-spending `POST /monitoring/promote-candidate`.

---

## Sources wired up

| Code(s) | Source | Adapter | Type | Enabled | robots.txt |
|---|---|---|---|---|---|
| 14 laws (PDPL, LABOR, PAYMENTS, AML, CFT, FRAUD, CREDIT, FINCOS, BCL, REFIN, SIFI, ETRANS, COMPANIES, CIVIL) | Bureau of Experts / National legislation DB — `laws.boe.gov.sa` | `boe` | html | ✅ yes | allowed: `/BoeLaws/` pages, `Crawl-delay: 10` (honored) |

**National Center for Legislation** = the Bureau of Experts legislation database (`laws.boe.gov.sa`).
There is no separate NCL site to crawl; the `ncl` adapter name is an **alias for `boe`**. The
National Platform (`my.gov.sa/rules`) only re-surfaces the same BOE data.

## Sources pending (adapter built, robots-checked, DISABLED until live structure verified)

| Code | Source | Adapter | Type | robots.txt | What's left before enabling |
|---|---|---|---|---|---|
| `MOJ-UPDATES` | Ministry of Justice — `moj.gov.sa` | `moj` | html | allowed (`User-agent: *`, no Disallow) | Confirm the real content URL + article container selector; the parser falls back to the heuristic Arabic article splitter. Note: primary MOJ law texts (Civil Transactions) already come via `boe`; this source is for MOJ-published circulars/updates. |
| `CMA-RULEBOOK` | Capital Market Authority — `cma.gov.sa` (`cma.org.sa` 301→ here) | `cma` | html | allowed for content; SharePoint infra paths disallowed (`/_layouts/`, `/search/`, `/Pages/Results.aspx`, …) and guarded in-adapter | Confirm rulebook content URL + SharePoint content selector. Some CMA regs are PDFs → may need a pdf-kind variant. |
| `UQN-GAZETTE` | Umm Al-Qura official gazette — `uqn.gov.sa` | `uqn` | pdf | allowed for content (blocks `?page=`/`?redirect=`/`/ajax/`, some bots; Twitterbot `Crawl-delay: 25`, honored) | Gazette issues are PDFs; the adapter fetches + extracts text (pypdf) then splits by article. Issues are **issue-based** (many regs per PDF), so article-level segmentation needs a verification pass before enabling. |

**SAMA** (`rulebook.sama.gov.sa`) is deliberately NOT in this pipeline — `robots.txt` is
`Disallow: /` and it filters by request signature. Handled separately via Claude in Chrome. A
placeholder scaffold exists at `scripts/seed_data/corpus/sama/` but is not fetched here.

---

## Current gaps

1. **Live-structure verification for the 3 new adapters.** Their fetch mechanism + robots status
   are verified; the article-level PARSE selectors are best-effort. Each needs one pass against a
   live page to confirm the selector and article segmentation, then flip `enabled: true`.
2. **Runtime deps not yet in the API image.** `run-check`'s browser fetch needs
   `playwright` + `chromium` (`python -m playwright install chromium`) and `lxml` (now in
   `requirements.txt`) in the API/worker image; `pypdf` is already present. Until then the browser
   fetch degrades gracefully to "fetch failed" (all-None), never crashing. In the sovereign
   deployment this fetch should run inside the egress-controlled sandbox (nftables allowlist
   already includes `laws.boe.gov.sa`; add `moj.gov.sa` / `cma.gov.sa` / `uqn.gov.sa` before
   enabling those).
3. **Scheduling is manual by design** (per current decision). The function is written so wiring a
   scheduler later is additive (call `run-check` from cron/arq) — not done now.
4. **UQN PDF article segmentation** is heuristic (gazette PDFs aren't cleanly article-delimited).

---

## How to add a new source later

1. **Check `robots.txt` first.** If the target disallows automated access, stop and flag it — do
   not build around it (that's why SAMA is excluded).
2. **Add the egress domain** to `sandboxes/research-agent/allowlist.yaml` if running in the
   sovereign sandbox.
3. **Write an adapter** in `apps/api/app/services/monitoring/adapters/<name>.py` subclassing
   `SourceAdapter`:
   - set `name`, `robots_status`, `kind` (`html` | `pdf`), and for html a `content_selector`;
   - implement `parse(raw) -> list[Article]` (split by `article_ref`); pdf adapters also
     implement `fetch_pdf(url)`. Reuse `_text.split_arabic_articles` as a fallback.
4. **Register it** in `apps/api/app/services/monitoring/adapters/__init__.py`.
5. **Add a source row** to `scripts/seed_data/corpus/_sources.yaml` with `adapter:` and a content
   `url`. Start with `enabled: false`.
6. **Verify parse** against a live page, then set `enabled: true`.
7. Everything downstream — hashing, `build_changes` diff, `monitoring_diffs`, promote → LLM impact,
   verify gate, pgvector ingest, retrieval + citation — is source-agnostic and needs no changes.

## Ingest runbook (fill the corpus)

All ingestion runs on the VM (needs the DB + embedder). Migrations 0007–0012 must be applied
first. Replace the compose prefix `CC` below:
`CC = docker compose -f docker-compose.yml -f docker-compose.prod.yml`

### 0. Pull + migrate + rebuild (once)
```bash
ssh ydet@20.244.108.2
cd ~/sanad && git pull --ff-only
cd infra
$CC build migrate && $CC run --rm migrate          # apply 0007–0012
$CC build api                                       # bake new _sources.yaml + lxml into the image
```

### A. Official BOE laws (verbatim, tier=official_fetch — CITABLE)
Fetches the 13 new laws from the gazette (10s crawl-delay each ≈ 3 min) and ingests them; the
existing 14 dedup-skip by content hash. Runs fetch+ingest in one container so the fetched YAMLs
are visible to the ingest step:
```bash
$CC run --rm api bash -lc "\
  python scripts/fetch_all_laws.py --only VAT,INCTAX,CUSTOMS,COMPET,BANKRUPT,COMCOURT,GOVPROC,INSURANCE,COMREG,COMPLEDGE,FRANCHISE,TASATTUR,COMAGENCY && \
  python scripts/ingest_regulations.py --trust-official-source scripts/seed_data/corpus/"
```
(If the api container has no outbound internet, run `fetch_all_laws.py` on the VM host in a venv
with `pip install lxml pyyaml`, commit the YAMLs, rebuild api, then run only the ingest step.)
Verify: `curl -s https://oursanad.dev/api/backend/admin/corpus` (or the Admin → Corpus screen)
should show ~27 regulations.

### B. Kaggle / third-party dataset (tier=unverified_third_party — SEARCHABLE, NOT citable)
Needs your Kaggle token at `~/.kaggle/kaggle.json`.
```bash
pip install kaggle
kaggle datasets download -d <owner>/<slug> -p ~/kag --unzip
cd ~/sanad/infra
$CC run --rm -v ~/kag:/data api python scripts/ingest_kaggle.py /data/<file>.csv \
  --code KAG-BOG --name-ar "قضايا ديوان المظالم" --text-col <text_column> \
  --dataset-url https://www.kaggle.com/datasets/<owner>/<slug>
```
These rows are searchable in Evidence but the citation gate blocks them from findings until a
reviewer verifies them against the official text (promoting the tier).

### C. Re-check allowed domains (before/after adding sources)
```bash
$CC run --rm api python scripts/check_allowlist_robots.py
```

## Architecture reference

- Adapters: `apps/api/app/services/monitoring/adapters/` (`base.py`, `boe.py`, `moj.py`, `cma.py`,
  `uqn.py`, `_text.py`).
- Dispatch: `apps/api/app/services/monitoring/detection.py` → `fetch_live_articles` (HTML sources
  share one headless Chromium via `scripts/playwright_fetch.BrowserFetcher`; PDF sources fetch
  their own bytes).
- Diff + persistence + two-stage gate: `apps/api/app/routers/monitoring.py`
  (`/run-check`, `/diffs`, `/promote-candidate`), `monitoring_diffs` table.
- Evidence store + retrieval: `regulation_versions` (pgvector, `content_hash`, `verification_tier`,
  `source_url`, `effective_date`), `apps/api/app/services/retrieval/`, citation gate
  `apps/api/app/services/citations/gate.py`.
