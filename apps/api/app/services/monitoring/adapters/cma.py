"""Capital Market Authority (cma.gov.sa — note cma.org.sa 301-redirects here).

robots.txt: `User-agent: *` disallows SharePoint infrastructure only (/_layouts/, /search/,
/Pages/Results.aspx, /bin/, /App_Data/, /App_Code/, /aspnet_client/). Regulation/rulebook
CONTENT pages are permitted — adapters must target content URLs, never those infra paths.

The CMA rulebook is a SharePoint site; article-level markup is NOT yet verified. This adapter
reads the SharePoint content region and falls back to the heuristic Arabic article splitter.
Registered but shipped DISABLED until verified against live pages. Some CMA regulations are
PDFs; those would use a pdf-kind variant (see the UQN adapter for the pdf pattern).
"""
from __future__ import annotations

from app.services.monitoring.adapters._text import split_arabic_articles
from app.services.monitoring.adapters.base import Article, SourceAdapter

# Paths robots.txt disallows — a guard so this adapter can never be pointed at them.
DISALLOWED_PREFIXES = (
    "/_layouts/", "/_vti_bin/", "/_catalogs/", "/search/", "/Pages/Results.aspx",
    "/bin/", "/App_Data/", "/App_Code/", "/aspnet_client/",
)


class CmaAdapter(SourceAdapter):
    name = "cma"
    robots_status = "allowed — cma.gov.sa permits content; SharePoint infra paths disallowed (guarded)"
    kind = "html"
    content_selector = "#contentBox, .ms-rtestate-field, main"  # unverified; refine before enabling

    def parse(self, raw: str | bytes) -> list[Article]:
        from lxml import html as lxml_html

        page = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
        doc = lxml_html.fromstring(page)
        nodes = doc.xpath(
            "//*[contains(@class,'ms-rtestate-field')] | //*[@id='contentBox'] | //main"
        ) or [doc]
        text = "\n".join(n.text_content() for n in nodes)
        return split_arabic_articles(text)
