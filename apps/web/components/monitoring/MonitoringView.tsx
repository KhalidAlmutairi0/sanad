"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/ui/Header";
import { useApp } from "@/lib/i18n";
import { apiGet, apiPost } from "@/lib/api";
import { DEMO_EVENTS } from "@/lib/demo";
import type { MonitoringEvent } from "@/types";

function VerifyForm({ eventId, demo, onDone }: { eventId: string; demo: boolean; onDone: () => void }) {
  const { dict } = useApp();
  const [articleRef, setArticleRef] = useState("");
  const [text, setText] = useState("");
  const [source, setSource] = useState("https://sdaia.gov.sa/");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    if (!demo) {
      await apiPost(`/monitoring/events/${eventId}/verify`, {
        regulation_version: { article_ref: articleRef, article_text_ar: text, source_url: source },
      }).catch(() => null);
    }
    onDone();
  }

  return (
    <form onSubmit={submit} className="mt-3 grid gap-2 rounded-chip border border-line bg-paper p-3">
      <input value={articleRef} onChange={(e) => setArticleRef(e.target.value)} required
        placeholder="Article 29" dir="ltr"
        className="rounded-chip border border-line bg-surface px-3 py-2 text-label text-ink" />
      <textarea value={text} onChange={(e) => setText(e.target.value)} required rows={2}
        placeholder="نص المادة المحدّث"
        className="rounded-chip border border-line bg-surface px-3 py-2 text-label text-ink" />
      <div className="flex justify-end">
        <button type="submit" disabled={busy}
          className="rounded-chip bg-orange px-4 py-2 text-label text-white disabled:opacity-50">
          {dict.monitoring.verify}
        </button>
      </div>
    </form>
  );
}

export function MonitoringView({ demo = false }: { demo?: boolean }) {
  const { dict } = useApp();
  const [items, setItems] = useState<MonitoringEvent[]>(demo ? DEMO_EVENTS : []);
  const [loading, setLoading] = useState(!demo);
  const [openId, setOpenId] = useState<string | null>(null);

  function load() {
    if (demo) return;
    apiGet<{ items: MonitoringEvent[] }>("/monitoring/events")
      .then((d) => setItems(d.items))
      .finally(() => setLoading(false));
  }
  useEffect(load, [demo]);

  function markVerified(id: string) {
    setItems((xs) => xs.map((e) => (e.id === id ? { ...e, status: "verified" } : e)));
    setOpenId(null);
    if (!demo) load();
  }

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-reading px-6 py-12">
        <h1 className="text-h1 font-semibold text-ink">{dict.monitoring.title}</h1>
        {loading ? (
          <p className="mt-8 text-body text-muted">{dict.common.loading}</p>
        ) : items.length === 0 ? (
          <p className="mt-12 rounded-card border border-dashed border-line p-12 text-center text-body text-muted">
            {dict.monitoring.empty}
          </p>
        ) : (
          <div className="mt-8 divide-y divide-line rounded-card border border-line bg-surface">
            {items.map((e) => (
              <div key={e.id} className="px-6 py-4">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-body text-ink">
                      {e.regulation_code}
                      {e.change_type ? ` · ${dict.monitoring.changeTypes[e.change_type as keyof typeof dict.monitoring.changeTypes] ?? e.change_type}` : ""}
                    </p>
                    <p className="mt-1 text-caption text-muted">{e.impact_summary_ar}</p>
                  </div>
                  {e.status === "detected" ? (
                    <button
                      onClick={() => setOpenId(openId === e.id ? null : e.id)}
                      className="rounded-chip border border-severity-high px-4 py-2 text-label text-severity-high"
                    >
                      {dict.monitoring.verify}
                    </button>
                  ) : (
                    <span className="text-label text-severity-ok">{dict.monitoring.verified}</span>
                  )}
                </div>
                {openId === e.id && <VerifyForm eventId={e.id} demo={demo} onDone={() => markVerified(e.id)} />}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
