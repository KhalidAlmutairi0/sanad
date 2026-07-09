"use client";

import { useApp } from "@/lib/i18n";

const TONE: Record<string, string> = {
  GO: "border-severity-ok text-severity-ok",
  REVIEW: "border-severity-high text-severity-high",
  STOP: "border-severity-critical text-severity-critical",
};

export function RadarPill({ verdict }: { verdict: "GO" | "REVIEW" | "STOP" }) {
  const { dict } = useApp();
  return (
    <span className="inline-flex flex-col items-center">
      <span className={`rounded-chip border px-6 py-2 text-label font-medium ${TONE[verdict] ?? ""}`}>
        {dict.verdict[verdict]}
      </span>
      <span className="mt-2 text-caption text-muted">{dict.review.radar}</span>
    </span>
  );
}
