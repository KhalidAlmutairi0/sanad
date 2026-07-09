import type { Severity } from "@/types";

// Single large mono numeral 0-100, thin arc in a severity-derived color, calm not gauge-y.
function arcColor(score: number): string {
  if (score >= 80) return "var(--sanad-ok)";
  if (score >= 60) return "var(--sanad-medium)";
  if (score >= 40) return "var(--sanad-high)";
  return "var(--sanad-critical)";
}

export function ReadinessDial({ score, label }: { score: number | null; label: string }) {
  const value = score ?? 0;
  const r = 52;
  const circ = 2 * Math.PI * r;
  const dash = (value / 100) * circ;
  const color = score === null ? "var(--sanad-line)" : arcColor(value);

  return (
    <div className="flex flex-col items-center">
      <svg width="140" height="140" viewBox="0 0 140 140" role="img" aria-label={`${label}: ${score ?? "—"}`}>
        <circle cx="70" cy="70" r={r} fill="none" stroke="var(--sanad-line)" strokeWidth="6" />
        <circle
          cx="70"
          cy="70"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circ}`}
          transform="rotate(-90 70 70)"
        />
        <text
          x="70"
          y="78"
          textAnchor="middle"
          className="tabular"
          style={{ fontFamily: "var(--font-plex-mono)", fontSize: "2rem", fontWeight: 500, fill: "var(--sanad-ink)" }}
        >
          {score === null ? "—" : score}
        </text>
      </svg>
      <span className="mt-2 text-caption text-muted">{label}</span>
    </div>
  );
}

export type { Severity };
