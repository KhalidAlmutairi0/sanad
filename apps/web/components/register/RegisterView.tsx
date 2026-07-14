"use client";

import { useEffect, useState } from "react";
import { AppLayout, SourceChip } from "@/components/design/Shared";
import { apiGet } from "@/lib/api";
import type { Obligation } from "@/types";

const STATUS: Record<Obligation["status"], { label: string; cls: string }> = {
  open: { label: "مفتوح", cls: "border-muted-foreground text-muted-foreground" },
  in_progress: { label: "قيد التنفيذ", cls: "border-[#D4812A] text-[#D4812A]" },
  met: { label: "مكتمل", cls: "border-primary text-primary" },
  overdue: { label: "متأخر", cls: "border-destructive text-destructive" },
};

export function RegisterView() {
  const [items, setItems] = useState<Obligation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<{ items: Obligation[] }>("/obligations").then((d) => setItems(d.items)).finally(() => setLoading(false));
  }, []);

  return (
    <AppLayout>
      <div className="space-y-6 flex flex-col min-h-[calc(100vh-9rem)]">
        <div className="flex items-center justify-between border-b border-border pb-6 shrink-0">
          <div>
            <h1 className="text-2xl font-bold mb-1">سجل الالتزامات التنظيمية</h1>
            <p className="text-[13px] text-muted-foreground font-mono">{items.length} ACTIVE OBLIGATIONS</p>
          </div>
        </div>

        <div className="bg-card border border-border rounded-xl overflow-hidden flex-1 flex flex-col min-h-0">
          {loading ? (
            <div className="p-12 text-center text-muted-foreground">جاري التحميل…</div>
          ) : items.length === 0 ? (
            <div className="p-12 text-center text-muted-foreground">ما فيه التزامات مسجّلة حتى الآن.</div>
          ) : (
            <div className="overflow-auto flex-1">
              <table className="w-full text-sm text-right">
                <thead className="bg-background/50 border-b border-border text-muted-foreground text-[13px] sticky top-0 z-10">
                  <tr>
                    <th className="p-4 font-normal min-w-[300px]">الالتزام</th>
                    <th className="p-4 font-normal whitespace-nowrap">الموعد</th>
                    <th className="p-4 font-normal whitespace-nowrap">الحالة</th>
                    <th className="p-4 font-normal whitespace-nowrap">المصدر</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {items.map((o) => (
                    <tr key={o.id} className="hover:bg-background/30 transition-colors group">
                      <td className="p-4 leading-relaxed group-hover:text-primary transition-colors">{o.title_ar}</td>
                      <td className="p-4 align-top pt-5 text-muted-foreground font-mono tnum">{o.due_date ?? "—"}</td>
                      <td className="p-4 align-top pt-5">
                        <span className={`px-2 py-1 text-[11px] rounded border ${STATUS[o.status].cls}`}>{STATUS[o.status].label}</span>
                      </td>
                      <td className="p-4 align-top pt-5">
                        <SourceChip text={`${o.citation.regulation_code} · ${o.citation.article_ref}`} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
