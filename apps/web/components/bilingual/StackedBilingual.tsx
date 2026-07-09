// Stacked bilingual, never inline-mixed: full Arabic block then full English block, each in
// its own direction (AGENTS.md bilingual rules). No Arabic and Latin on the same line.
export function StackedBilingual({
  ar,
  en,
  className = "",
}: {
  ar: string | null | undefined;
  en: string | null | undefined;
  className?: string;
}) {
  return (
    <div className={className}>
      {ar && (
        <p dir="rtl" className="text-body text-ink">
          {ar}
        </p>
      )}
      {en && (
        <p dir="ltr" className="mt-2 text-body text-muted">
          {en}
        </p>
      )}
    </div>
  );
}
