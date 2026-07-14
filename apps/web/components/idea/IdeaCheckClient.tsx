"use client";

import { useEffect, useRef, useState } from "react";
import { AppLayout, Button, SourceChip } from "@/components/design/Shared";
import { apiGet, apiPost } from "@/lib/api";

interface IdeaCitation {
  regulation_version_id: string;
  regulation_code: string;
  article_ref: string;
  source_url: string;
}
interface IdeaDetail {
  id: string;
  status: "submitted" | "generated" | "reviewed";
  report_ar: string | null;
  report_en: string | null;
  citations: IdeaCitation[];
}

export function IdeaCheckClient() {
  const [idea, setIdea] = useState("");
  const [busy, setBusy] = useState(false);
  const [detail, setDetail] = useState<IdeaDetail | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => { if (timer.current) clearInterval(timer.current); }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (idea.trim().length < 10) return;
    setBusy(true);
    setDetail(null);
    const created = await apiPost<{ id: string }>("/idea-checks", { idea_text: idea });
    timer.current = setInterval(async () => {
      const d = await apiGet<IdeaDetail>(`/idea-checks/${created.id}`);
      if (d.status !== "submitted") {
        if (timer.current) clearInterval(timer.current);
        setDetail(d);
        setBusy(false);
      }
    }, 2000);
  }

  return (
    <AppLayout>
      <div className="max-w-[800px] mx-auto space-y-8">
        <div>
          <h1 className="text-2xl font-bold mb-2">فحص الفكرة</h1>
          <p className="text-[15px] text-muted-foreground">اكتب فكرتك بكلام واضح لنحلّلها أمام الأنظمة واللوائح قبل أن تبدأ بالتنفيذ.</p>
        </div>

        <form onSubmit={submit} className="space-y-4">
          <textarea value={idea} onChange={(e) => setIdea(e.target.value)}
            placeholder="مثال: تطبيق إقراض رقمي للأفراد يعتمد على بيانات بديلة من الجوال لتقييم الجدارة الائتمانية، وتخزين البيانات في سحابة خارج المملكة..."
            className="w-full h-40 bg-card border border-border rounded-xl p-4 text-[15px] leading-relaxed resize-none focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all" />
          <div className="flex justify-end">
            <Button type="submit" disabled={busy || idea.trim().length < 10}>{busy ? "جاري الفحص…" : "أرسل للفحص"}</Button>
          </div>
        </form>

        {busy && (
          <div className="bg-card border border-border p-12 rounded-xl flex flex-col items-center justify-center">
            <div className="w-12 h-12 border-4 border-border border-t-primary rounded-full animate-spin mb-4" />
            <p className="text-muted-foreground font-mono text-[13px]">جاري استخراج السياق والمطابقة…</p>
          </div>
        )}

        {!detail && !busy && (
          <div className="py-16 text-center text-muted-foreground">أرسل فكرة وبتوصلك مراجعة امتثال مع مصادرها.</div>
        )}

        {detail && (
          <div className="space-y-6">
            <div className="bg-card border border-border p-6 rounded-xl">
              <h3 className="font-bold mb-4">التقرير</h3>
              {detail.report_ar && <p dir="rtl" className="whitespace-pre-wrap text-[15px] leading-[1.9] text-foreground">{detail.report_ar}</p>}
              {detail.report_en && <p dir="ltr" className="whitespace-pre-wrap text-[14px] leading-[1.7] text-muted-foreground mt-6 pt-6 border-t border-border">{detail.report_en}</p>}
            </div>
            {detail.citations.length > 0 && (
              <div className="bg-card border border-border p-6 rounded-xl">
                <h3 className="font-bold mb-4">المصادر</h3>
                <div className="flex flex-wrap gap-3">
                  {detail.citations.map((c) => (
                    <SourceChip key={c.regulation_version_id} text={`${c.regulation_code} · ${c.article_ref}`} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
