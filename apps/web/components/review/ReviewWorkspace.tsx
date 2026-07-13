"use client";

import { useApp } from "@/lib/i18n";
import type { Clause, ContractDetail, Finding } from "@/types";
import { ReadinessDial } from "@/components/score/ReadinessDial";
import { FindingCard } from "@/components/findings/FindingCard";
import { RadarPill } from "./RadarPill";

interface Props {
  contract: ContractDetail;
  clauses: Clause[];
  findings: Finding[];
  verdict: "GO" | "REVIEW" | "STOP";
}

export function ReviewWorkspace({ contract, clauses, findings, verdict }: Props) {
  const { dict } = useApp();

  return (
    <div>
      <div className="flex flex-col items-center justify-between gap-8 border-b border-line pb-8 sm:flex-row">
        <div>
          <h1 className="text-h1 font-semibold text-ink">{contract.title}</h1>
          {contract.ocr_used && (
            <span className="mt-2 inline-block rounded-chip bg-orange-bg px-3 py-1 text-caption text-orange-ink">
              {dict.review.ocrDocument}
            </span>
          )}
        </div>
        <div className="flex items-center gap-12">
          <RadarPill verdict={verdict} />
          <ReadinessDial score={contract.readiness_score} label={dict.review.reviewedOnly} />
        </div>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* Contract pane */}
        <section>
          <h2 className="mb-4 text-h3 text-muted">{dict.review.contractPane}</h2>
          <div className="max-h-[70vh] space-y-4 overflow-y-auto rounded-card border border-line bg-surface p-6">
            {clauses.map((c) => (
              <p key={c.id} dir={c.text_ar ? "rtl" : "ltr"} className="text-body leading-8 text-ink">
                <span className="me-2 text-caption text-muted tabular">{c.ordinal}.</span>
                {c.text_ar ?? c.text_en}
              </p>
            ))}
          </div>
        </section>

        {/* Findings pane */}
        <section>
          <h2 className="mb-4 text-h3 text-muted">{dict.review.findingsPane}</h2>
          {findings.length === 0 ? (
            <p className="rounded-card border border-dashed border-line p-12 text-center text-body text-muted">
              {dict.review.noFindings}
            </p>
          ) : (
            <div className="space-y-4">
              {findings.map((f) => (
                <FindingCard key={f.id} finding={f} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
