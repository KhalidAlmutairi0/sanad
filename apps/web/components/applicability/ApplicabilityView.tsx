"use client";

import { useEffect, useState } from "react";
import { AppLayout, MonoChip, SourceChip } from "@/components/design/Shared";
import { apiGet } from "@/lib/api";
import type { ApplicabilityFinding, ContractApplicability } from "@/types";

const FLAG_AR: Record<ApplicabilityFinding["flag"], string> = {
  NEEDS_REMEDIATION: "بحاجة إلى معالجة",
  EXEMPT_GRANDFATHERED: "معفاة (حقوق مكتسبة)",
  ALREADY_COMPLIANT: "ملتزم مسبقاً",
  MUST_COMPLY: "خاضع للتطبيق",
  NOT_APPLICABLE: "لا ينطبق",
};

function FindingRow({ f }: { f: ApplicabilityFinding }) {
  return (
    <div className="bg-card border border-border rounded-xl p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <span className="text-[13px] font-medium">{FLAG_AR[f.flag]}</span>
        {f.due_date && (
          <span className="text-[12px] font-mono px-2 py-0.5 rounded border border-destructive text-destructive">
            قبل {f.due_date}
          </span>
        )}
      </div>
      {f.clause && (
        <p dir="rtl" className="text-[14px] leading-[1.9] text-muted-foreground">
          <span className="font-mono text-[12px] text-muted-foreground/70 ms-2">بند {f.clause.ordinal}·</span>
          {f.clause.text_ar}
        </p>
      )}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-muted-foreground">المادة</span>
          <SourceChip text={`${f.source_article.regulation_code} · ${f.source_article.article_ref}`} withLine />
        </div>
        {f.classification_citation && (
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-muted-foreground">مصدر التصنيف</span>
            <SourceChip text={`${f.classification_citation.regulation_code} · ${f.classification_citation.article_ref}`} />
          </div>
        )}
      </div>
    </div>
  );
}

function Bucket({ title, tone, items }: {
  title: string; tone: "red" | "green" | "muted"; items: ApplicabilityFinding[];
}) {
  const [open, setOpen] = useState(tone === "red");
  const border = tone === "red" ? "border-destructive/40" : tone === "green" ? "border-[#2F7D5B]/40" : "border-border";
  const dot = tone === "red" ? "bg-destructive" : tone === "green" ? "bg-[#2F7D5B]" : "bg-muted-foreground";
  return (
    <div className={`border ${border} rounded-2xl overflow-hidden`}>
      <button onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-muted/30 transition-colors">
        <div className="flex items-center gap-3">
          <span className={`w-2.5 h-2.5 rounded-full ${dot}`} />
          <span className="font-bold text-[15px]">{title}</span>
          <MonoChip className="text-muted-foreground">{items.length}</MonoChip>
        </div>
        <span className="text-muted-foreground text-[13px]">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="p-4 pt-0 space-y-3">
          {items.length === 0 ? (
            <p className="text-[13px] text-muted-foreground text-center py-4">لا عناصر.</p>
          ) : (
            items.map((f, i) => <FindingRow key={`${f.source_article.regulation_version_id}-${f.clause?.clause_id ?? i}`} f={f} />)
          )}
        </div>
      )}
    </div>
  );
}

export function ApplicabilityView({ contractId }: { contractId: string }) {
  const [data, setData] = useState<ContractApplicability | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<ContractApplicability>(`/applicability/contract/${contractId}`)
      .then(setData).finally(() => setLoading(false));
  }, [contractId]);

  return (
    <AppLayout>
      <div className="max-w-[900px] mx-auto space-y-6">
        <div className="border-b border-border pb-6">
          <h1 className="text-2xl font-bold mb-2">انطباق التحديثات التنظيمية</h1>
          <p className="text-[15px] text-muted-foreground">
            هل تنطبق الأنظمة المُحدَّثة على هذا العقد القائم، وما الإجراء المطلوب؟ تُقيَّم فقط التصنيفات المُراجَعة بشرياً.
          </p>
        </div>

        {loading ? (
          <div className="py-16 text-center text-muted-foreground">جاري التحميل…</div>
        ) : !data ? (
          <div className="py-16 text-center text-muted-foreground">تعذّر التحميل.</div>
        ) : data.signed_date === null ? (
          <div className="bg-[#B4842F]/8 border border-[#B4842F]/30 text-[#B4842F] rounded-xl px-4 py-3 text-[14px]">
            تاريخ توقيع العقد غير محدد — لا يمكن تقييم الانطباق حتى يُسجَّل تاريخ التوقيع.
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between text-[13px] text-muted-foreground">
              <span>تاريخ التوقيع: <span className="font-mono">{data.signed_date}</span></span>
              {data.pending_review > 0 && (
                <span className="text-[#B4842F]">{data.pending_review} تصنيف بانتظار مراجعة قانونية</span>
              )}
            </div>
            <Bucket title="بحاجة إلى معالجة" tone="red" items={data.needs_remediation} />
            <Bucket title="معفاة / حقوق مكتسبة" tone="green" items={data.grandfathered} />
            <Bucket title="ملتزم — لا إجراء" tone="muted" items={data.compliant} />
          </>
        )}
      </div>
    </AppLayout>
  );
}
