"use client";

import { useApp } from "@/lib/i18n";

export function ContractsHeading() {
  const { dict } = useApp();
  return <h1 className="text-h1 font-semibold text-ink">{dict.contracts.title}</h1>;
}

export function EmptyState() {
  const { dict } = useApp();
  return (
    <p className="mt-12 rounded-card border border-dashed border-line p-12 text-center text-body text-muted">
      {dict.contracts.empty}
    </p>
  );
}
