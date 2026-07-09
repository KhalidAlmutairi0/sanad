"use client";

import { useEffect, useRef, useState } from "react";
import { Header } from "@/components/ui/Header";
import { useApp } from "@/lib/i18n";
import { apiGet, apiPost } from "@/lib/api";

interface IdeaCitation {
  regulation_version_id: string;
  regulation_code: string;
  article_ref: string;
  source_url: string;
}
interface IdeaDetail {
  id: string;
  status: "submitted" | "generated" | "reviewed";
  report_ar: string | null;
  report_en: string | null;
  citations: IdeaCitation[];
}

export default function IdeaCheckPage() {
  const { dict } = useApp();
  const [idea, setIdea] = useState("");
  const [busy, setBusy] = useState(false);
  const [detail, setDetail] = useState<IdeaDetail | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => { if (timer.current) clearInterval(timer.current); }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (idea.trim().length < 10) return;
    setBusy(true);
    setDetail(null);
    const created = await apiPost<{ id: string }>("/idea-checks", { idea_text: idea });
    timer.current = setInterval(async () => {
      const d = await apiGet<IdeaDetail>(`/idea-checks/${created.id}`);
      if (d.status !== "submitted") {
        if (timer.current) clearInterval(timer.current);
        setDetail(d);
        setBusy(false);
      }
    }, 2000);
  }

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-reading px-6 py-12">
        <h1 className="text-h1 font-semibold text-ink">{dict.ideaCheck.title}</h1>

        <form onSubmit={submit} className="mt-8">
          <label className="block">
            <span className="text-label text-muted">{dict.ideaCheck.prompt}</span>
            <textarea
              value={idea}
              onChange={(e) => setIdea(e.target.value)}
              rows={5}
              className="mt-2 w-full rounded-card border border-line bg-surface p-4 text-body leading-8 text-ink"
              required
            />
          </label>
          <button
            type="submit"
            disabled={busy || idea.trim().length < 10}
            className="mt-4 rounded-chip bg-orange px-6 py-3 text-label text-white disabled:opacity-50"
          >
            {busy ? dict.ideaCheck.generating : dict.ideaCheck.submit}
          </button>
        </form>

        {!detail && !busy && (
          <p className="mt-12 text-body text-muted">{dict.ideaCheck.empty}</p>
        )}

        {detail && (
          <section className="mt-12 rounded-card border border-line bg-surface p-8">
            <h2 className="text-h3 text-muted">{dict.ideaCheck.report}</h2>
            {detail.report_ar && (
              <p dir="rtl" className="mt-4 whitespace-pre-wrap text-body leading-8 text-ink">
                {detail.report_ar}
              </p>
            )}
            {detail.report_en && (
              <p dir="ltr" className="mt-6 whitespace-pre-wrap border-t border-line pt-6 text-body leading-8 text-muted">
                {detail.report_en}
              </p>
            )}

            {detail.citations.length > 0 && (
              <div className="mt-8 border-t border-line pt-6">
                <h3 className="mb-3 text-label text-orange-ink">{dict.ideaCheck.citations}</h3>
                <ul className="space-y-2">
                  {detail.citations.map((c) => (
                    <li key={c.regulation_version_id}>
                      <a
                        href={c.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 rounded-chip border border-orange px-3 py-1 text-label text-orange-ink hover:bg-orange-bg"
                      >
                        <span aria-hidden>◆</span>
                        {c.regulation_code} {c.article_ref}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
