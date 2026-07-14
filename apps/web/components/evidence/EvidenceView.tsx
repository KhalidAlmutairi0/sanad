"use client";

import { useState } from "react";
import { AppLayout, Button, MonoChip } from "@/components/design/Shared";
import { apiGet } from "@/lib/api";
import type { EvidenceSearchItem } from "@/types";

export function EvidenceView() {
  const [q, setQ] = useState("");
  const [items, setItems] = useState<EvidenceSearchItem[] | null>(null);
  const [busy, setBusy] = useState(false);

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (q.trim().length < 2) return;
    setBusy(true);
    try {
      const d = await apiGet<{ items: EvidenceSearchItem[] }>(`/evidence/search?q=${encodeURIComponent(q)}`);
      setItems(d.items);
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppLayout>
      <div className="max-w-[1000px] mx-auto space-y-8">
        <div>
          <h1 className="text-2xl font-bold mb-2">مخزن الأدلة</h1>
          <p className="text-[15px] text-muted-foreground">ابحث في جميع الأنظمة واللوائح المالية المخزّنة، مع فهمٍ سياقي للمصطلحات المترادفة.</p>
        </div>

        <form onSubmit={search} className="flex gap-4">
          <input type="text" value={q} onChange={(e) => setQ(e.target.value)}
            placeholder="ابحث في الأنظمة والمواد... (مثال: مدة الاحتفاظ ببيانات العملاء)"
            className="flex-1 bg-card border border-border rounded-lg px-4 py-3 text-[15px] outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all" />
          <Button type="submit" disabled={busy} className="px-8">{busy ? "…" : "بحث"}</Button>
        </form>

        {items === null ? (
          <div className="py-24 text-center text-muted-foreground">اكتب كلمة للبحث في المواد النظامية المخزّنة.</div>
        ) : items.length === 0 ? (
          <div className="py-24 text-center text-muted-foreground">ما فيه نتائج.</div>
        ) : (
          <div className="space-y-4">
            <div className="text-[13px] text-muted-foreground font-mono mb-6">FOUND {items.length} RESULTS</div>
            {items.map((res) => (
              <div key={res.regulation_version_id} className="bg-card border border-border p-6 rounded-xl hover:border-primary/50 transition-colors group">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-[13px] font-bold text-foreground">{res.regulation_code}</span>
                    <MonoChip>{res.article_ref}</MonoChip>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-muted-foreground font-mono">MATCH</span>
                    <span className={`font-mono text-[13px] ${res.score > 0.9 ? "text-primary" : "text-foreground"}`}>{Math.round(res.score * 100)}%</span>
                  </div>
                </div>
                <p dir="rtl" className="text-[15px] leading-relaxed text-muted-foreground group-hover:text-foreground transition-colors">{res.snippet_ar}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
