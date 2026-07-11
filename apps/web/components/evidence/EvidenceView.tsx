"use client";

import { useState } from "react";
import { Header } from "@/components/ui/Header";
import { SourceChip } from "@/components/findings/SourceChip";
import { useApp } from "@/lib/i18n";
import { apiGet } from "@/lib/api";
import { DEMO_EVIDENCE } from "@/lib/demo";
import type { EvidenceSearchItem } from "@/types";

export function EvidenceView({ demo = false }: { demo?: boolean }) {
  const { dict } = useApp();
  const [q, setQ] = useState("");
  const [items, setItems] = useState<EvidenceSearchItem[] | null>(null);
  const [busy, setBusy] = useState(false);

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (q.trim().length < 2) return;
    setBusy(true);
    if (demo) {
      const needle = q.trim();
      setItems(DEMO_EVIDENCE.filter((i) => i.snippet_ar.includes(needle) || i.regulation_code.includes(needle)) || DEMO_EVIDENCE);
      setBusy(false);
      return;
    }
    const d = await apiGet<{ items: EvidenceSearchItem[] }>(`/evidence/search?q=${encodeURIComponent(q)}`);
    setItems(d.items);
    setBusy(false);
  }

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-reading px-6 py-12">
        <h1 className="text-h1 font-semibold text-ink">{dict.evidence.title}</h1>
        <form onSubmit={search} className="mt-8 flex gap-3">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={dict.evidence.prompt}
            className="flex-1 rounded-chip border border-line bg-surface px-4 py-3 text-body text-ink"
          />
          <button type="submit" disabled={busy} className="rounded-chip bg-orange px-6 py-3 text-label text-white disabled:opacity-50">
            {dict.evidence.search}
          </button>
        </form>

        {items === null ? (
          <p className="mt-12 text-body text-muted">{dict.evidence.empty}</p>
        ) : items.length === 0 ? (
          <p className="mt-12 text-body text-muted">{dict.evidence.noResults}</p>
        ) : (
          <div className="mt-8 space-y-4">
            {items.map((i) => (
              <article key={i.regulation_version_id} className="rounded-card border border-line bg-surface p-6">
                <div className="flex items-center justify-between gap-4">
                  <SourceChip citation={{ regulation_code: i.regulation_code, article_ref: i.article_ref, source_url: "#" }} />
                  <span className="tabular text-caption text-muted" style={{ fontFamily: "var(--font-plex-mono)" }}>
                    {dict.evidence.score} {Math.round(i.score * 100)}%
                  </span>
                </div>
                <p dir="rtl" className="mt-3 text-body leading-8 text-ink">{i.snippet_ar}</p>
              </article>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
