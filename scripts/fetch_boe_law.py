"""Fetch a Saudi law from the official gazette (laws.boe.gov.sa) and emit corpus YAML with
VERBATIM article text.

Legitimacy: laws.boe.gov.sa/robots.txt permits crawling law pages (only /admin, /search,
/comment etc. are disallowed) with Crawl-delay: 10. This tool honors that delay and sends an
identifying User-Agent. It fetches the official public gazette text only. Output is written
`verified: false` — a human still confirms each article against the source before it can be
cited (AGENTS.md #5). We never fabricate text; every article is parsed from the page.

Usage:
    python scripts/fetch_boe_law.py <law_url> --code PDPL --name-ar "..." --name-en "..." \
        --authority SDAIA --out scripts/seed_data/corpus/PDPL.yaml
    # or parse a already-downloaded file instead of fetching:
    python scripts/fetch_boe_law.py <law_url> --html /tmp/pdpl.html --code PDPL ...
"""
from __future__ import annotations

import argparse
import sys
import time
import urllib.request

import lxml.html
import yaml

CRAWL_DELAY_SECONDS = 10
UA = "SANAD-compliance-research/1.0 (regulatory corpus; contact: khalid.a.almutairi0@gmail.com)"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def parse_articles(html: str) -> list[dict]:
    """Extract main articles from a boe law page.

    Each article is a `div.article_item` containing an `h3.center` header (المادة X) and the
    body. Amendment-history popups live in separate `div.article_item_popup` blocks under a
    hidden `.popup-list` — those are dropped so only the current article text is captured.
    """
    doc = lxml.html.fromstring(html)
    articles: list[dict] = []
    # Main article containers carry class "article_item"; the current-text header is an
    # <h3 class="center">. Amendment-history popups use a plain <h3> inside .popup-list.
    for node in doc.xpath("//div[contains(concat(' ', normalize-space(@class), ' '), ' article_item ')]"):
        header = node.xpath("./h3[contains(concat(' ', normalize-space(@class), ' '), ' center ')]")
        if not header:
            continue  # skip popups / non-article items
        ref = header[0].text_content().strip().rstrip(":").strip()
        # Drop nested hidden popup-lists, the header, and the button bar before reading body.
        for drop in node.xpath(
            ".//*[contains(concat(' ', normalize-space(@class), ' '), ' popup-list ')]"
            " | ./h3[contains(concat(' ', normalize-space(@class), ' '), ' center ')]"
            " | .//*[contains(concat(' ', normalize-space(@class), ' '), ' article_btns ')]"
        ):
            parent = drop.getparent()
            if parent is not None:
                parent.remove(drop)
        text = " ".join(node.text_content().split())
        if ref and text:
            articles.append({"article_ref": ref, "article_text_ar": text})
    return articles


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--html", help="parse this local file instead of fetching")
    ap.add_argument("--code", required=True)
    ap.add_argument("--name-ar", required=True)
    ap.add_argument("--name-en", required=True)
    ap.add_argument("--authority", required=True)
    ap.add_argument("--source-domain", default="laws.boe.gov.sa")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    if args.html:
        html = open(args.html, encoding="utf-8").read()
    else:
        time.sleep(CRAWL_DELAY_SECONDS)  # honor robots Crawl-delay
        html = fetch(args.url)

    articles = parse_articles(html)
    if not articles:
        print("No articles parsed — the page structure may have changed.", file=sys.stderr)
        return 1

    doc = {
        "regulation": {
            "code": args.code,
            "name_ar": args.name_ar,
            "name_en": args.name_en,
            "authority": args.authority,
            "source_domain": args.source_domain,
        },
        "articles": [
            {
                "article_ref": a["article_ref"],
                "article_text_ar": a["article_text_ar"],
                "source_url": args.url,
                "verified": False,  # human gate: confirm against source before citing
            }
            for a in articles
        ],
    }
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(f"# {args.name_en} ({args.name_ar}) — fetched VERBATIM from {args.source_domain}.\n")
        f.write("# Text is parsed from the official gazette page; verified: false until a human\n")
        f.write("# confirms each article against source_url (AGENTS.md #5). Not fabricated.\n")
        yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False, width=1000)
    print(f"Wrote {len(articles)} articles to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
