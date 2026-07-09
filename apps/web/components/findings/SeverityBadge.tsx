import type { Severity } from "@/types";

const DOT: Record<Severity, string> = {
  critical: "bg-severity-critical",
  high: "bg-severity-high",
  medium: "bg-severity-medium",
  low: "bg-severity-low",
};
const TEXT: Record<Severity, string> = {
  critical: "text-severity-critical",
  high: "text-severity-high",
  medium: "text-severity-medium",
  low: "text-severity-low",
};

// Small filled dot + label. Never a full red banner — the tool stays calm (style-guide).
export function SeverityBadge({ severity, label }: { severity: Severity; label: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-label">
      <span className={`h-2 w-2 rounded-full ${DOT[severity]}`} aria-hidden />
      <span className={TEXT[severity]}>{label}</span>
    </span>
  );
}
