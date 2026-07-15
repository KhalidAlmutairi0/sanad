"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { apiPost } from "@/lib/api";
import { DealBreakerPill, ReadinessGauge, MonoChip, SourceChip } from "@/components/design/Shared";
import type { Clause, ContractDetail, Finding } from "@/types";

interface Props {
  contract: ContractDetail;
  clauses: Clause[];
  findings: Finding[];
  verdict: "GO" | "REVIEW" | "STOP";
}

type Sev = "red" | "amber" | "muted";

function sevOf(s: string): Sev {
  if (s === "critical") return "red";
  if (s === "high" || s === "medium") return "amber";
  return "muted";
}

const SEV_AR: Record<string, string> = { critical: "حرجة", high: "عالية", medium: "متوسطة", low: "منخفضة" };
const dotClass: Record<Sev, string> = { red: "bg-destructive", amber: "bg-[#D4812A]", muted: "bg-muted-foreground" };
const sevText: Record<Sev, string> = { red: "text-destructive", amber: "text-[#D4812A]", muted: "text-muted-foreground" };

export function ReviewWorkspace({ contract, clauses, findings, verdict }: Props) {
  const router = useRouter();
  const [items, setItems] = useState<Finding[]>(findings);
  const [activeId, setActiveId] = useState<string | null>(null);
  const clauseRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  async function review(id: string, decision: "accepted" | "rejected") {
    setItems((xs) => xs.map((f) => (f.id === id ? { ...f, review_status: decision } : f)));
    await apiPost(`/findings/${id}/review`, { decision }).catch(() => null);
    router.refresh();
  }

  function selectFinding(f: Finding) {
    setActiveId(f.id);
    if (f.clause_id) {
      const el = clauseRefs.current.get(f.clause_id);
      el?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  // Highest-severity finding per clause, plus which clause the active finding points at.
  const clauseSev = new Map<string, Sev>();
  let activeClauseId: string | null = null;
  for (const f of items) {
    if (f.id === activeId) activeClauseId = f.clause_id;
    if (f.clause_id) {
      const cur = clauseSev.get(f.clause_id);
      const s = sevOf(f.severity);
      if (!cur || (s === "red" && cur !== "red")) clauseSev.set(f.clause_id, s);
    }
  }

  return (
    <div className="flex flex-col md:h-[calc(100vh-8rem)] md:overflow-hidden">
      <div className="flex items-center justify-between border-b border-border pb-6 mb-6 shrink-0 flex-wrap gap-4">
        <div className="flex items-center gap-4 flex-wrap">
          <h1 className="text-2xl font-bold">{contract.title}</h1>
          <MonoChip className="text-muted-foreground">{contract.ocr_used ? "مستند ممسوح · OCR" : "مستند رقمي"}</MonoChip>
          <DealBreakerPill state={verdict} />
        </div>
        <ReadinessGauge value={contract.readiness_score ?? 0} className="scale-90 origin-right" />
      </div>

      <div className="flex flex-col md:flex-row gap-6 flex-1 min-h-0">
        {/* Contract text — independently scrollable */}
        <div className="w-full md:w-1/2 bg-card border border-border rounded-xl p-6 md:overflow-y-auto">
          <div className="space-y-5 text-[15px] leading-[2]">
            {clauses.length === 0 && <p className="text-muted-foreground">لا يوجد نص مستخرج.</p>}
            {clauses.map((c) => {
              const sev = clauseSev.get(c.id);
              const isActive = c.id === activeClauseId;
              const insufficient = c.retrieval_insufficient && !sev;
              const box = sev === "red"
                ? "p-4 -mx-4 rounded-lg bg-primary/5 border border-primary/30"
                : sev === "amber"
                ? "p-4 -mx-4 rounded-lg bg-[#D4812A]/5 border border-[#D4812A]/30"
                : insufficient
                ? "p-4 -mx-4 rounded-lg bg-muted-foreground/[0.04] border border-dashed border-muted-foreground/30"
                : "";
              const activeRing = isActive ? "ring-2 ring-primary ring-offset-2 ring-offset-card p-4 -mx-4 rounded-lg" : "";
              const numColor = sev === "red" ? "text-primary" : sev === "amber" ? "text-[#D4812A]" : "text-muted-foreground";
              return (
                <div
                  key={c.id}
                  ref={(el) => { if (el) clauseRefs.current.set(c.id, el); }}
                  className={`flex gap-4 scroll-mt-4 transition-all ${box} ${activeRing}`}
                  dir={c.text_ar ? "rtl" : "ltr"}
                >
                  <span className={`font-mono mt-1 shrink-0 ${insufficient ? "text-muted-foreground/70" : numColor}`}>
                    {insufficient ? "?" : `${c.ordinal}.`}
                  </span>
                  <div className="flex-1">
                    <p>{c.text_ar ?? c.text_en}</p>
                    {insufficient && (
                      <span className="mt-2 inline-block text-[12px] text-muted-foreground border border-dashed border-muted-foreground/40 rounded px-2 py-0.5">
                        لم يُعثر على مادة نظامية مطابقة — لم يُقيَّم هذا البند
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Findings — one place, independently scrollable */}
        <div className="w-full md:w-1/2 flex flex-col min-h-0">
          <div className="flex items-center justify-between shrink-0 mb-3 px-1">
            <h2 className="text-[15px] font-bold">الملاحظات <span className="text-muted-foreground font-mono text-[13px]">({items.length})</span></h2>
            <span className="text-[12px] text-muted-foreground">اضغط ملاحظة لإبرازها في العقد</span>
          </div>
          <div className="md:overflow-y-auto md:flex-1 space-y-4 pe-1">
            {items.length === 0 ? (
              <div className="bg-card border border-dashed border-border rounded-xl p-12 text-center text-muted-foreground">
                ما فيه ملاحظات على هذا العقد.
              </div>
            ) : (
              items.map((f) => {
                const sev = sevOf(f.severity);
                const decided = f.review_status !== "pending";
                const isActive = f.id === activeId;
                const lowConf = f.confidence_tier === "low" || f.confidence_tier === "uncertain";
                return (
                  <div
                    key={f.id}
                    onClick={() => selectFinding(f)}
                    className={`bg-card border rounded-xl p-5 flex flex-col gap-3 cursor-pointer transition-all ${
                      isActive ? "border-primary ring-1 ring-primary" : lowConf ? "border-dashed border-[#B4842F]/60 hover:border-[#B4842F]" : "border-border hover:border-primary/50"
                    } ${decided ? "opacity-60" : ""}`}
                  >
                    {lowConf && (
                      <div className="flex items-center gap-2 text-[12px] text-[#B4842F] bg-[#B4842F]/8 border border-[#B4842F]/25 rounded-md px-3 py-1.5 -mt-1">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                        <span className="font-medium">ضعيف التطابق — يتطلب تحقق يدوي</span>
                      </div>
                    )}
                    <div className="flex items-center gap-3 flex-wrap">
                      <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${dotClass[sev]}`} />
                      <span className={`text-[12px] font-medium ${sevText[sev]}`}>{SEV_AR[f.severity] ?? f.severity}</span>
                      {f.category === "sharia" && (
                        <span className="text-[11px] px-2 py-0.5 rounded border border-[#2F7D5B]/40 text-[#2F7D5B]">شرعي</span>
                      )}
                      {f.clause_id && <MonoChip className="text-muted-foreground ms-auto">بند مرتبط</MonoChip>}
                    </div>

                    <h3 className="text-[16px] font-bold leading-[1.7]">{f.title_ar}</h3>
                    {f.explanation_ar && <p className="text-[14px] leading-[1.9] text-muted-foreground">{f.explanation_ar}</p>}
                    {f.violation_cost_ar && (
                      <p className="text-[13px] text-destructive/90 bg-destructive/5 border border-destructive/20 rounded-md px-3 py-2">
                        {f.violation_cost_ar}
                      </p>
                    )}

                    <div className="mt-1 flex items-center justify-between gap-3 flex-wrap">
                      <SourceChip text={`${f.citation.regulation_code} · ${f.citation.article_ref}`} withLine />
                      {!decided ? (
                        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                          <button onClick={() => review(f.id, "rejected")} className="text-[13px] px-3 py-1.5 rounded-md border border-border hover:bg-border transition-colors">رفض</button>
                          <button onClick={() => review(f.id, "accepted")} className="text-[13px] px-3 py-1.5 rounded-md bg-primary text-primary-foreground font-medium hover:opacity-90 transition-opacity">تطبيق</button>
                        </div>
                      ) : (
                        <span className={`text-[13px] font-medium ${f.review_status === "accepted" ? "text-primary" : "text-muted-foreground"}`}>
                          {f.review_status === "accepted" ? "مُطبّقة" : "مرفوضة"}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
