"use client";

import { useEffect, useRef, useState } from "react";
import { AppLayout, MonoChip, SourceChip } from "@/components/design/Shared";
import { apiGet } from "@/lib/api";
import type { VendorResults, VendorScorecardItem, VendorView } from "@/types";

const STATUS_STYLE: Record<VendorScorecardItem["status"], string> = {
  present: "text-[#2F7D5B]",
  weak: "text-[#B4842F]",
  missing: "text-destructive",
};
const STATUS_AR: Record<VendorScorecardItem["status"], string> = {
  present: "متوفر", weak: "ضعيف", missing: "مفقود",
};

function cell(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "boolean") return v ? "نعم" : "لا";
  if (typeof v === "number") return v.toLocaleString("en-US");
  return String(v);
}

function VendorGateCard({ v }: { v: VendorView }) {
  const passed = v.stage1_passed;
  const border = passed === false ? "border-destructive/50" : passed ? "border-[#2F7D5B]/50" : "border-border";
  return (
    <div className={`bg-card border ${border} rounded-xl p-5`}>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <span className="font-bold text-[15px]">{v.vendor_name}</span>
          {passed === true && <span className="text-[12px] px-2 py-0.5 rounded-full border border-[#2F7D5B] text-[#2F7D5B]">اجتاز البوابة</span>}
          {passed === false && <span className="text-[12px] px-2 py-0.5 rounded-full border border-destructive text-destructive">مُستبعَد</span>}
          {passed === null && <span className="text-[12px] text-muted-foreground">قيد المعالجة…</span>}
        </div>
        {v.security_flag_count > 0 && (
          <MonoChip className="text-[#B4842F] border-[#B4842F]/40">{v.security_flag_count} تنبيه أمني</MonoChip>
        )}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {v.scorecard.map((s) => (
          <div key={s.requirement_id} className="flex items-center justify-between gap-2 text-[13px] border border-border rounded-md px-3 py-2">
            <div className="flex items-center gap-2 min-w-0">
              <span className={`font-mono text-[11px] ${s.mandatory ? "text-foreground" : "text-muted-foreground"}`}>{s.section}</span>
              <span className="truncate text-muted-foreground">{s.description_ar}</span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className={STATUS_STYLE[s.status]}>{STATUS_AR[s.status]}</span>
              {s.document_location && <span className="text-[11px] text-muted-foreground font-mono">{s.document_location}</span>}
            </div>
          </div>
        ))}
      </div>
      {v.exclusions.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2 items-center">
          <span className="text-[12px] text-destructive">سبب الاستبعاد:</span>
          {v.exclusions.map((e) => (
            <SourceChip key={e.requirement_id} text={`SAMA-Outsourcing · القسم ${e.section}${e.sama_source_pending ? " (النص قيد الإضافة)" : ""}`} />
          ))}
        </div>
      )}
    </div>
  );
}

export function VendorResultsView({ evaluationId }: { evaluationId: string }) {
  const [data, setData] = useState<VendorResults | null>(null);
  const [loading, setLoading] = useState(true);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    function load() {
      apiGet<VendorResults>(`/vendor-evaluations/${evaluationId}`).then((d) => {
        setData(d);
        setLoading(false);
        if (d.status === "done" && timer.current) { clearInterval(timer.current); timer.current = null; }
      }).catch(() => setLoading(false));
    }
    load();
    timer.current = setInterval(load, 3000);
    return () => { if (timer.current) clearInterval(timer.current); };
  }, [evaluationId]);

  if (loading) return <AppLayout><div className="py-16 text-center text-muted-foreground">جاري التحميل…</div></AppLayout>;
  if (!data) return <AppLayout><div className="py-16 text-center text-muted-foreground">تعذّر التحميل.</div></AppLayout>;

  return (
    <AppLayout>
      <div className="max-w-[1000px] mx-auto space-y-8">
        <div className="bg-muted/40 border border-border rounded-lg px-4 py-3 text-[13px] text-muted-foreground">
          {data.banner}
        </div>

        <div className="flex items-center justify-between border-b border-border pb-6">
          <div>
            <h1 className="text-2xl font-bold mb-1">{data.title}</h1>
            <p className="text-[13px] text-muted-foreground font-mono">
              {data.status === "done" ? "اكتملت المقارنة" : data.status === "comparing" ? "جاري التقييم…" : data.status}
            </p>
          </div>
        </div>

        {/* Stage 1 — compliance gate (top, most evidentiary weight) */}
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#2F7D5B]" />
            <h2 className="text-[16px] font-bold">المرحلة 1 — بوابة الامتثال (ساما للإسناد)</h2>
            <span className="text-[12px] text-muted-foreground">مصدرها مواد ساما المسماة</span>
          </div>
          {data.vendors.map((v) => <VendorGateCard key={v.submission_id} v={v} />)}
        </section>

        {/* Stage 2 — comparison (extracted; only passers) */}
        {data.comparison && data.comparison.vendor_ids.length > 0 && (
          <section className="space-y-4">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#2563EB]" />
              <h2 className="text-[16px] font-bold">المرحلة 2 — المقارنة</h2>
              <span className="text-[11px] px-2 py-0.5 rounded border border-[#2563EB]/40 text-[#2563EB]">بيانات مستخرجة</span>
            </div>
            {data.comparison.currency_mismatch && (
              <div className="text-[13px] text-[#B4842F] bg-[#B4842F]/8 border border-[#B4842F]/25 rounded-md px-3 py-2">
                عملات مختلفة بين العروض — المقارنة السعرية المباشرة غير دقيقة دون سعر صرف موحّد.
              </div>
            )}
            <div className="bg-card border border-border rounded-xl overflow-x-auto">
              <table className="w-full text-[14px] text-right">
                <thead className="bg-background/50 border-b border-border text-muted-foreground text-[13px]">
                  <tr>
                    <th className="p-3 font-normal">البُعد</th>
                    {data.comparison.vendor_ids.map((vid) => <th key={vid} className="p-3 font-medium">{vid}</th>)}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {data.comparison.rows.map((row, i) => (
                    <tr key={i}>
                      <td className="p-3 text-muted-foreground">
                        {row.dimension}
                        {row.delta_note && <span className="block text-[11px] text-primary">{row.delta_note}</span>}
                      </td>
                      {data.comparison!.vendor_ids.map((vid) => (
                        <td key={vid} className="p-3 font-mono tnum">{cell(row.values[vid])}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-[12px] text-muted-foreground">لا توجد درجة إجمالية واحدة — تُعرض الفروقات فقط، والقرار للمراجع البشري.</p>
          </section>
        )}

        {/* Self-reported background — as claimed, unverified */}
        {data.self_reported.length > 0 && (
          <section className="space-y-4">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-muted-foreground" />
              <h2 className="text-[16px] font-bold">خلفية الشركة</h2>
              <span className="text-[11px] px-2 py-0.5 rounded border border-muted-foreground/40 text-muted-foreground"
                title="منقولة من عرض المورد، غير محقّقة من مصدر مستقل">كما صرّح المورد</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {data.self_reported.map((s) => (
                <div key={s.vendor_name} className="bg-muted/30 border border-dashed border-border rounded-xl p-4">
                  <p className="font-bold text-[14px] mb-2">{s.vendor_name}</p>
                  <div className="text-[13px] text-muted-foreground space-y-1">
                    {Object.entries(s.background).filter(([k]) => k !== "label" && k !== "note").map(([k, v]) => (
                      <div key={k} className="flex justify-between gap-2"><span>{k}</span><span className="font-mono">{cell(v)}</span></div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </AppLayout>
  );
}
