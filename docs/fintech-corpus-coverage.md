# Saudi FinTech Compliance Corpus — authorities, sources, coverage

Scope: every authority and document set a Saudi FinTech company needs for compliance. This is
the living inventory + coverage report. It records what is auto-fetchable verbatim, what is
inventoried-but-blocked (needs manual download), and gaps.

**Sourcing rule:** official government/regulator sources only. Verbatim text is obtained by
(a) auto-fetch from `laws.boe.gov.sa` (robots-permitted, 10s delay) or (b) manual download of
official PDFs. We never scrape sites whose robots.txt disallows it, never use unofficial
copies/blogs/summaries, and never fabricate text. Auto-fetched text is tagged `official_fetch`
until human-reviewed (see AGENTS.md #5).

## Fetchability of official sources (checked 2026-07-13, via robots.txt)

| Source | Hosts | Policy | Status |
|---|---|---|---|
| laws.boe.gov.sa | The binding **laws** (all authorities) | permits law pages, Crawl-delay 10 | **auto-fetch (verbatim)** |
| zatca.gov.sa | Tax/VAT/e-invoicing rules | robots permits content (system paths blocked) | pages fetchable; most rules are PDFs → manual |
| nca.gov.sa | Cybersecurity controls (ECC, CCC, etc.) | robots permits content | controls are PDFs → manual |
| mc.gov.sa | Commercial/company rules | robots permits content (SharePoint sys blocked) | mixed; PDFs → manual |
| misa.gov.sa | Investment licensing | robots permits, Crawl-delay 30 | pages fetchable |
| saip.gov.sa | IP | robots permits | pages fetchable |
| rulebook.sama.gov.sa | SAMA rulebook (frameworks, circulars) | **Disallow: /** | blocked — manual download only |
| sama.gov.sa | SAMA PDFs | curl blocked (000) | manual download |
| cma.org.sa | CMA rulebooks | 301 redirect / blocked | manual download |
| sdaia.gov.sa | PDPL exec regs | curl blocked (000) | manual download |
| cst.gov.sa / chi.gov.sa | Telecom / health insurance | 301 redirect | manual download |

## Authorities and their FinTech-relevant document sets

Legend: **[boe]** auto-fetchable law · **[man]** manual download (blocked/PDF) · status of each.

### 1. SAMA — Saudi Central Bank (the primary FinTech regulator)
- **[boe]** Banking Control Law · Finance Companies Control Law · Real Estate Finance Law · Finance Lease Law · **Law of Payments and Payment Services** · Credit Information Law · Anti-Money Laundering Law · Law on Combating the Financing of Terrorism — all on the gazette, fetchable.
- **[man]** SAMA rulebook frameworks/circulars (rulebook.sama.gov.sa, Disallow:/): Rules on Outsourcing, Cyber Security Framework, Business Continuity, Consumer Protection, Counter-Fraud, IT Governance, Rules for Licensing Payment Institutions, Open Banking Framework, BNPL rules, SVF rules. → manual PDF.

### 2. CMA — Capital Market Authority
- **[boe]** Capital Market Law · Investment Funds / Companies Laws where gazetted.
- **[man]** CMA rulebooks (cma.org.sa): Authorised Persons Regulations, Securities Business Regulations, Market Conduct, Investment Accounts Instructions, Fintech ExPermit / crowdfunding rules. → manual PDF.

### 3. SDAIA / NDMO — data protection
- **[boe]** Personal Data Protection Law (PDPL) — fetched ✅ (43 articles).
- **[man]** PDPL Implementing Regulations + Data Transfer Regulations (sdaia.gov.sa PDFs). → manual.

### 4. ZATCA — Zakat, Tax and Customs
- **[boe]** VAT Law · Income Tax Law · Zakat rules where gazetted.
- **[man]** VAT Implementing Regulations, **E-Invoicing (Fatoora) Regulation + technical standards**. → manual/PDF.

### 5. NCA — National Cybersecurity Authority
- **[man]** Essential Cybersecurity Controls (ECC), Cloud Cybersecurity Controls (CCC), Critical Systems Controls, Data Cybersecurity Controls. → PDFs.

### 6. CST — Communications, Space & Technology
- **[boe]** Telecom/IT laws where gazetted. **[man]** cloud/data rules → manual.

### 7. Ministry of Commerce
- **[boe]** Companies Law · Commercial Register Law · Commercial Fraud/Anti-Concealment where gazetted. **[man]** e-commerce rules → mixed.

### 8. MISA — Ministry of Investment
- **[man]** Foreign investment licensing rules (misa.gov.sa). → pages fetchable / PDF.

### 9. Others (lower FinTech relevance, inventory only)
- SAIP (IP), Council of Health Insurance, Saudi Business Center (licensing aggregator), GAZT-successor items, National Anti-Commercial-Concealment.

## Coverage status

| Regulation | Authority | Articles | Text | Method |
|---|---|---|---|---|
| PDPL | SDAIA | 43 | verbatim | boe ✅ |
| Labor Law | MHRSD | 250 | verbatim | boe ✅ |
| Banking Control Law | SAMA | 26 | scaffold | boe (pending fetch) |
| Rules on Outsourcing | SAMA | 53 | scaffold | rulebook blocked → manual |

**Auto-fetchable next (boe), highest FinTech value:** Law of Payments and Payment Services,
Finance Companies Control Law, Anti-Money Laundering Law, Combating Financing of Terrorism Law,
Credit Information Law, Capital Market Law, Companies Law.

## Honest gaps (cannot be auto-fetched)
- SAMA rulebook frameworks & circulars (Disallow:/) — the detailed prudential/conduct rules.
- CMA rulebooks — blocked host.
- NCA cybersecurity controls, ZATCA e-invoicing standards, PDPL implementing regs — PDFs on blocked/redirecting hosts.
These require official PDF download (a person saves the file) before ingestion. Inventoried
above with their authorities; text is not fabricated.
