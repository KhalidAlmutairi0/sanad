"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { Finding } from "@/types";
import { useApp } from "@/lib/i18n";
import { apiPost } from "@/lib/api";
import { CitationChip } from "./CitationChip";
import { SeverityBadge } from "./SeverityBadge";
import { StackedBilingual } from "../bilingual/StackedBilingual";

function money(n: number | null): string | null {
  return n === null ? null : new Intl.NumberFormat("en-US").format(n);
}

export function FindingCard({ finding }: { finding: Finding }) {
  const { dict } = useApp();
  const router = useRouter();
  const [status, setStatus] = useState(finding.review_status);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function review(decision: "accepted" | "rejected") {
    setBusy(true);
    setError(null);
    try {
      await apiPost(`/findings/${finding.id}/review`, { decision });
      setStatus(decision);
      router.refresh(); // recomputed readiness score + contract status
    } catch (e) {
      setError((e as Error & { code?: string }).code ?? "error");
      setBusy(false);
    }
  }

  const min = money(finding.violation_cost_min);
  const max = money(finding.violation_cost_max);

  return (
    <article className="rounded-card border border-line bg-surface p-6">
      <div className="flex items-start justify-between gap-4">
        <SeverityBadge severity={finding.severity} label={dict.severity[finding.severity]} />
        <CitationChip citation={finding.citation} />
      </div>

      <StackedBilingual ar={finding.title_ar} en={finding.title_en} className="mt-4 font-medium" />

      {(finding.explanation_ar || finding.explanation_en) && (
        <div className="mt-4 border-t border-line pt-4">
          <p className="mb-2 text-caption text-muted">{dict.review.explanation}</p>
          <StackedBilingual ar={finding.explanation_ar} en={finding.explanation_en} />
        </div>
      )}

      {(finding.violation_cost_ar || min) && (
        <div className="mt-4 border-t border-line pt-4">
          <p className="mb-1 text-caption text-muted">{dict.review.violationCost}</p>
          {finding.violation_cost_ar && (
            <p dir="rtl" className="text-body text-ink">
              {finding.violation_cost_ar}
            </p>
          )}
          {min && (
            <p className="tabular mt-1 text-label text-severity-high" style={{ fontFamily: "var(--font-plex-mono)" }}>
              {min}{max && max !== min ? ` – ${max}` : ""} SAR
            </p>
          )}
        </div>
      )}

      <div className="mt-6 flex items-center gap-3">
        {status === "pending" ? (
          <>
            <button
              type="button"
              disabled={busy}
              onClick={() => review("accepted")}
              className="rounded-chip bg-severity-ok px-6 py-2 text-label text-white disabled:opacity-50"
            >
              {dict.review.accept}
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => review("rejected")}
              className="rounded-chip border border-line px-6 py-2 text-label text-ink disabled:opacity-50"
            >
              {dict.review.reject}
            </button>
          </>
        ) : (
          <span className={`text-label ${status === "accepted" ? "text-severity-ok" : "text-muted"}`}>
            {status === "accepted" ? dict.review.accepted : dict.review.rejected}
          </span>
        )}
        {error && <span className="text-label text-severity-critical">{error}</span>}
      </div>
    </article>
  );
}
