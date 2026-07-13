"use client";

import { useState } from "react";
import type { Citation } from "@/types";
import { useApp } from "@/lib/i18n";

// THE signature element. Every finding carries this orange-outlined chip; opening it shows
// the exact stored article text + source + version date. A finding without a chip is a UI
// impossibility (Zero Unsourced Findings, made visible).
export function CitationChip({ citation }: { citation: Citation }) {
  const { dict } = useApp();
  const [open, setOpen] = useState(false);

  return (
    <span className="relative inline-block">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center gap-1 rounded-chip border border-orange px-3 py-1 text-label text-orange-ink hover:bg-orange-bg"
        aria-expanded={open}
      >
        <span aria-hidden>◆</span>
        {citation.regulation_code} {citation.article_ref}
      </button>

      {open && (
        <div
          dir="rtl"
          className="absolute z-10 mt-2 w-[min(90vw,32rem)] rounded-card border border-line bg-surface p-6 shadow-lg"
          style={{ insetInlineStart: 0 }}
        >
          <div className="mb-3 flex items-center justify-between">
            <span className="text-label text-orange-ink">
              {citation.regulation_code} · {citation.article_ref}
            </span>
            <button type="button" onClick={() => setOpen(false)} className="text-muted" aria-label="close">
              ✕
            </button>
          </div>
          <p className="whitespace-pre-wrap text-body leading-8 text-ink">{citation.article_text_ar}</p>
          {citation.verification_tier === "official_fetch" && (
            <p className="mt-3 rounded-chip bg-orange-bg px-3 py-2 text-caption text-orange-ink">
              {dict.review.autoFetched}
            </p>
          )}
          <div className="mt-4 flex flex-wrap items-center gap-4 border-t border-line pt-3 text-caption text-muted">
            {citation.effective_date && (
              <span className="tabular">
                {dict.review.effectiveDate}: {citation.effective_date}
              </span>
            )}
            <a
              href={citation.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-orange-ink underline"
            >
              {dict.review.viewSource}
            </a>
          </div>
        </div>
      )}
    </span>
  );
}
