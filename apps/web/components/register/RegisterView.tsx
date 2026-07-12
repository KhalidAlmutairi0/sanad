"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/ui/Header";
import { SourceChip } from "@/components/findings/SourceChip";
import { useApp } from "@/lib/i18n";
import { apiGet } from "@/lib/api";
import type { Obligation } from "@/types";

const TONE: Record<Obligation["status"], string> = {
  open: "text-muted",
  in_progress: "text-severity-high",
  met: "text-severity-ok",
  overdue: "text-severity-critical",
};

export function RegisterView() {
  const { dict } = useApp();
  const [items, setItems] = useState<Obligation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<{ items: Obligation[] }>("/obligations")
      .then((d) => setItems(d.items))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-6xl px-6 py-12">
        <h1 className="text-h1 font-semibold text-ink">{dict.register.title}</h1>
        {loading ? (
          <p className="mt-8 text-body text-muted">{dict.common.loading}</p>
        ) : items.length === 0 ? (
          <p className="mt-12 rounded-card border border-dashed border-line p-12 text-center text-body text-muted">
            {dict.register.empty}
          </p>
        ) : (
          <div className="mt-8 overflow-x-auto rounded-card border border-line bg-surface">
            <table className="w-full text-label">
              <thead>
                <tr className="border-b border-line text-muted">
                  <th className="px-6 py-3 text-start font-medium">{dict.register.obligation}</th>
                  <th className="px-6 py-3 text-start font-medium">{dict.register.source}</th>
                  <th className="px-6 py-3 text-start font-medium">{dict.register.due}</th>
                  <th className="px-6 py-3 text-start font-medium">{dict.register.status}</th>
                </tr>
              </thead>
              <tbody>
                {items.map((o) => (
                  <tr key={o.id} className="border-b border-line last:border-0">
                    <td className="px-6 py-4 text-body text-ink">{o.title_ar}</td>
                    <td className="px-6 py-4"><SourceChip citation={o.citation} /></td>
                    <td className="px-6 py-4 tabular text-muted" style={{ fontFamily: "var(--font-plex-mono)" }}>
                      {o.due_date ?? "—"}
                    </td>
                    <td className={`px-6 py-4 ${TONE[o.status]}`}>{dict.register.statuses[o.status]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
