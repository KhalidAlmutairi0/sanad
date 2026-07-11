import type { SourceCitation } from "@/types";

// Lightweight citation chip (code + article) linking to the source. Used where the full
// stored article text isn't loaded (register, monitoring, evidence).
export function SourceChip({ citation }: { citation: Pick<SourceCitation, "regulation_code" | "article_ref" | "source_url"> }) {
  return (
    <a
      href={citation.source_url}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 rounded-chip border border-orange px-3 py-1 text-label text-orange-ink hover:bg-orange-bg"
    >
      <span aria-hidden>◆</span>
      {citation.regulation_code} {citation.article_ref}
    </a>
  );
}
