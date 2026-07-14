"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiPost } from "@/lib/api";
import { DealBreakerPill, ReadinessGauge, MonoChip, FindingCard } from "@/components/design/Shared";
import type { Clause, ContractDetail, Finding } from "@/types";

interface Props {
  contract: ContractDetail;
  clauses: Clause[];
  findings: Finding[];
  verdict: "GO" | "REVIEW" | "STOP";
}

function sevOf(s: string): "red" | "amber" | "muted" {
  if (s === "critical") return "red";
  if (s === "high" || s === "medium") return "amber";
  return "muted";
}

export function ReviewWorkspace({ contract, clauses, findings, verdict }: Props) {
  const router = useRouter();
  const [items, setItems] = useState<Finding[]>(findings);

  async function review(id: string, decision: "accepted" | "rejected") {
    setItems((xs) => xs.map((f) => (f.id === id ? { ...f, review_status: decision } : f)));
    await apiPost(`/findings/${id}/review`, { decision }).catch(() => null);
    router.refresh();
  }

  // Which clauses carry a finding (for highlighting the text pane).
  const clauseSev = new Map<string, "red" | "amber" | "muted">();
  for (const f of items) {
    if (f.clause_id) {
      const cur = clauseSev.get(f.clause_id);
      const s = sevOf(f.severity);
      if (!cur || (s === "red" && cur !== "red")) clauseSev.set(f.clause_id, s);
    }
  }

  return (
    <div className="flex flex-col min-h-[calc(100vh-9rem)]">
      <div className="flex items-center justify-between border-b border-border pb-6 mb-6 shrink-0 flex-wrap gap-4">
        <div className="flex items-center gap-4 flex-wrap">
          <h1 className="text-2xl font-bold">{contract.title}</h1>
          <MonoChip className="text-muted-foreground">{contract.ocr_used ? "مستند ممسوح · OCR" : "مستند رقمي"}</MonoChip>
          <DealBreakerPill state={verdict} />
        </div>
        <ReadinessGauge value={contract.readiness_score ?? 0} className="scale-90 origin-right" />
      </div>

      <div className="flex flex-col md:flex-row gap-6 flex-1 min-h-0">
        {/* Contract text */}
        <div className="w-full md:w-1/2 bg-card border border-border rounded-xl p-6 overflow-y-auto">
          <div className="space-y-5 text-[15px] leading-[2]">
            {clauses.length === 0 && <p className="text-muted-foreground">لا يوجد نص مستخرج.</p>}
            {clauses.map((c) => {
              const sev = clauseSev.get(c.id);
              const box = sev === "red"
                ? "p-4 -mx-4 rounded-lg bg-primary/5 border border-primary/30"
                : sev === "amber"
                ? "p-4 -mx-4 rounded-lg bg-[#D4812A]/5 border border-[#D4812A]/30"
                : "";
              const numColor = sev === "red" ? "text-primary" : sev === "amber" ? "text-[#D4812A]" : "text-muted-foreground";
              return (
                <div key={c.id} className={`flex gap-4 ${box}`} dir={c.text_ar ? "rtl" : "ltr"}>
                  <span className={`font-mono mt-1 ${numColor}`}>{c.ordinal}.</span>
                  <p>{c.text_ar ?? c.text_en}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Findings */}
        <div className="w-full md:w-1/2 overflow-y-auto ps-2 space-y-4">
          {items.length === 0 ? (
            <div className="bg-card border border-dashed border-border rounded-xl p-12 text-center text-muted-foreground">
              ما فيه ملاحظات على هذا العقد.
            </div>
          ) : (
            items.map((f) => (
              <FindingCard
                key={f.id}
                id={f.citation.regulation_code}
                severity={sevOf(f.severity)}
                text={f.title_ar}
                source={`${f.citation.regulation_code} · ${f.citation.article_ref}`}
                showActions={f.review_status === "pending"}
                onAccept={() => review(f.id, "accepted")}
                onReject={() => review(f.id, "rejected")}
                className={f.review_status !== "pending" ? "opacity-60" : ""}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
