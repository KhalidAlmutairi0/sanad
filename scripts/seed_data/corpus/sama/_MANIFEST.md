# SAMA rulebook ingestion manifest

Tracking the fetch of the whole SAMA rulebook (rulebook.sama.gov.sa) into corpus YAML.
Every article is fetched VERBATIM from the rulebook and stored `verified: false` until a
human reconciles it against the live page. Status: `todo` / `fetching` / `drafted` / `verified`.

## Category 1361 — Laws and Implementing Regulations

| # | Document | file | status |
|---|---|---|---|
| 1 | Saudi Central Bank Law | SAMA_central_bank_law.yaml | todo |
| 2 | Saudi Arabian Monetary Law | SAMA_monetary_law.yaml | todo |
| 3 | Banking Control Law | SAMA_banking_control_law.yaml | drafted (26 arts, scaffold) |
| 4 | Implementation Rules for Banking Control Law | SAMA_banking_control_impl.yaml | todo |
| 5 | Finance Companies Control Law | SAMA_finance_companies_law.yaml | todo |
| 6 | Implementing Regulation of the Finance Companies Control Law | SAMA_finance_companies_impl.yaml | todo |
| 7 | Real Estate Finance Law | SAMA_real_estate_finance_law.yaml | todo |
| 8 | Implementing Regulation of the Real Estate Finance Law | SAMA_real_estate_finance_impl.yaml | todo |
| 9 | Finance Lease Law | SAMA_finance_lease_law.yaml | todo |
| 10 | Implementing Regulation of the Finance Lease Law | SAMA_finance_lease_impl.yaml | todo |
| 11 | Law of Payments and Payment Services | SAMA_payments_law.yaml | todo |
| 12 | Implementing Regulations of Payments and Payment Services Law | SAMA_payments_impl.yaml | todo |
| 13 | Credit Information Law | SAMA_credit_info_law.yaml | todo |
| 14 | Implementing Regulations of Credit Information Law | SAMA_credit_info_impl.yaml | todo |
| 15 | Anti-Money Laundering Law | SAMA_aml_law.yaml | todo |
| 16 | Implementing Regulation to the Anti-Money Laundering Law | SAMA_aml_impl.yaml | todo |
| 17 | Law on Combating the Financing of Terrorism | SAMA_cft_law.yaml | todo |
| 18 | Implementing Regulations (Combating Terrorist Crimes and Financing) | SAMA_cft_impl.yaml | todo |
| 19 | Systemically Important Financial Institutions | SAMA_sifi.yaml | todo |
| 20 | Close-out Netting and related Collateral Arrangements Regulation | SAMA_closeout_netting.yaml | todo |

## Cross-sector (category 1362) — contract-relevant, prioritized

| Document | file | status |
|---|---|---|
| Rules on Outsourcing | SAMA_outsourcing.yaml | drafted (53 clauses, scaffold) |
| Consumer Protection and Financial Conduct | SAMA_consumer_protection.yaml | todo |
| Cyber Security Framework | SAMA_csf.yaml | todo |

## Remaining categories (to enumerate)

- 1362 All Financial Institutions (AML/CFT, Cyber Risk Control, Corporate Governance, Consumer Protection, General Provisions)
- 1363 Banking Sector
- 1365 Finance Sector
- 1366 Money Exchange Sector
- 1367 Payment Systems and PSPs
- 5902 Credit Bureaus
- 1368 Regulatory Sandbox
- node/10291 SAMA Circulars (chronological)
