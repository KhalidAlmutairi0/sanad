"use client";

import { useEffect, useState } from "react";
import { AppLayout, Button, MonoChip } from "@/components/design/Shared";
import { apiGet, apiPost } from "@/lib/api";
import type { MonitoringEvent } from "@/types";

const CHANGE_AR: Record<string, string> = { new_article: "مادة جديدة", amended: "تعديل", repealed: "إلغاء" };

function VerifyForm({ eventId, onDone }: { eventId: string; onDone: () => void }) {
  const [articleRef, setArticleRef] = useState("");
  const [text, setText] = useState("");
  const [source, setSource] = useState("https://sdaia.gov.sa/");
  const [busy, setBusy] = useState(false);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    await apiPost(`/monitoring/events/${eventId}/verify`, {
      regulation_version: { article_ref: articleRef, article_text_ar: text, source_url: source },
    }).catch(() => null);
    onDone();
  }
  return (
    <form onSubmit={submit} className="mt-4 grid gap-2 rounded-lg border border-border bg-background p-4">
      <input value={articleRef} onChange={(e) => setArticleRef(e.target.value)} required placeholder="المادة" dir="rtl"
        className="rounded-md border border-border bg-card px-3 py-2 text-[13px] outline-none focus:border-primary" />
      <textarea value={text} onChange={(e) => setText(e.target.value)} required rows={2} placeholder="نص المادة المحدّث" dir="rtl"
        className="rounded-md border border-border bg-card px-3 py-2 text-[13px] outline-none focus:border-primary" />
      <div className="flex justify-end"><Button type="submit" disabled={busy} className="h-9 px-4 text-[13px]">تأكيد التحقق</Button></div>
    </form>
  );
}

export function MonitoringView() {
  const [items, setItems] = useState<MonitoringEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [openId, setOpenId] = useState<string | null>(null);

  function load() {
    apiGet<{ items: MonitoringEvent[] }>("/monitoring/events").then((d) => setItems(d.items)).finally(() => setLoading(false));
  }
  useEffect(load, []);

  return (
    <AppLayout>
      <div className="max-w-[800px] mx-auto space-y-8">
        <div className="flex items-center justify-between border-b border-border pb-6">
          <div>
            <h1 className="text-2xl font-bold mb-2">رصد التحديثات التنظيمية</h1>
            <p className="text-[15px] text-muted-foreground">متابعة منتظمة للمصادر الرسمية، مع تقييم أثر كل تحديث على سجل التزاماتك.</p>
          </div>
          <div className="bg-primary/10 border border-primary/30 text-primary px-4 py-2 rounded-lg flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            <span className="text-[13px] font-mono">متابعة مستمرة</span>
          </div>
        </div>

        {loading ? (
          <div className="py-16 text-center text-muted-foreground">جاري التحميل…</div>
        ) : items.length === 0 ? (
          <div className="py-16 text-center text-muted-foreground">ما فيه تغييرات مرصودة حتى الآن.</div>
        ) : (
          <div className="space-y-6">
            {items.map((e) => {
              const isNew = e.status === "detected";
              return (
                <div key={e.id} className={`bg-card border ${isNew ? "border-primary/50" : "border-border"} p-6 rounded-xl relative group`}>
                  {isNew && <div className="absolute top-0 right-6 -translate-y-1/2 bg-background px-2 text-[10px] font-mono text-primary border border-primary/30 rounded">NEW</div>}
                  <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-center mb-4">
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-[15px]">{e.regulation_code}</span>
                      {e.change_type && (<><span className="w-1 h-1 rounded-full bg-border" /><span className="text-[13px] text-muted-foreground">{CHANGE_AR[e.change_type] ?? e.change_type}</span></>)}
                    </div>
                    <span className="text-[13px] text-muted-foreground font-mono">{e.detected_at?.slice(0, 10)}</span>
                  </div>
                  <p className="text-[15px] text-muted-foreground mb-6 leading-relaxed">{e.impact_summary_ar}</p>
                  <div className="flex justify-end">
                    {isNew ? (
                      <Button variant="primary" className="h-9 px-4 text-[13px]" onClick={() => setOpenId(openId === e.id ? null : e.id)}>تحقّق من الأثر</Button>
                    ) : (
                      <span className="text-[13px] text-primary font-mono">تم التحقق</span>
                    )}
                  </div>
                  {openId === e.id && <VerifyForm eventId={e.id} onDone={() => { setOpenId(null); load(); }} />}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
