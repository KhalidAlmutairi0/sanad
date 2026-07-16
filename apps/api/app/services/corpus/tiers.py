"""Verification tiers for corpus articles — the single source of truth for what may be CITED.

- human_verified      : a person reconciled the text against the official source. Citable.
- official_fetch      : parsed verbatim from the official gazette by the fetch tool. Citable
                        (owner policy trusts the official source), surfaced as auto-fetched.
- unverified_third_party : imported from a third-party dataset (e.g. Kaggle). Stored and
                        SEARCHABLE, but NOT citable — a finding can never rest on it until a
                        human verifies it against the official text (which promotes the tier).
"""
from __future__ import annotations

HUMAN_VERIFIED = "human_verified"
OFFICIAL_FETCH = "official_fetch"
UNVERIFIED_THIRD_PARTY = "unverified_third_party"

ALL_TIERS = (HUMAN_VERIFIED, OFFICIAL_FETCH, UNVERIFIED_THIRD_PARTY)
# Tiers a finding is allowed to cite. Quarantined third-party text is deliberately excluded.
CITABLE_TIERS = (HUMAN_VERIFIED, OFFICIAL_FETCH)
