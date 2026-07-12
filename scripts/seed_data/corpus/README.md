# Corpus format (one YAML file per regulation)

Each file describes one regulation and its articles. `scripts/ingest_regulations.py` loads
every `*.yaml` here into `regulation_versions`. Only articles with `verified: true` are
inserted — this is the human gate (AGENTS.md #5). Drafts stay `verified: false` until a
qualified person has reconciled the Arabic text against the official source.

```yaml
regulation:
  code: PDPL                       # stable short code, unique
  name_ar: نظام حماية البيانات الشخصية
  name_en: Personal Data Protection Law
  authority: SDAIA
  source_domain: sdaia.gov.sa

articles:
  - article_ref: "Article 1"       # as printed in the official text
    article_text_ar: |             # VERBATIM Arabic; never paraphrase
      نص المادة الرسمي هنا.
    article_text_en: |             # optional official/working English
      Official article text here.
    source_url: https://laws.boe.gov.sa/...   # deep link to the official source
    effective_date: 2023-09-14     # optional (ISO date)
    verified: false                # flip to true ONLY after human reconciliation
    verified_by_initials: KA       # who verified (required once verified: true)
```

Workflow: draft articles with `verified: false` (agent), a human reconciles each against the
official gazette and flips `verified: true` + initials, then run the ingester. Re-running is
idempotent (unchanged articles are skipped by content hash).
