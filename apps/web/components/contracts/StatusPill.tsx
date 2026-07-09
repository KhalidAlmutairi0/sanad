"use client";

import type { ContractStatus } from "@/types";
import { useApp } from "@/lib/i18n";

const TONE: Record<ContractStatus, string> = {
  uploaded: "text-muted",
  sanitizing: "text-muted",
  sanitized: "text-muted",
  extracting: "text-muted",
  reviewing: "text-severity-high",
  reviewed: "text-severity-ok",
  failed: "text-severity-critical",
};

export function StatusPill({ status }: { status: ContractStatus }) {
  const { dict } = useApp();
  return <span className={`text-label ${TONE[status]}`}>{dict.statuses[status]}</span>;
}
