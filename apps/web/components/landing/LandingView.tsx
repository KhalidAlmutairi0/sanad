"use client";

import Link from "next/link";
import { useApp } from "@/lib/i18n";

export function LandingView() {
  const { dict, toggleLocale, toggleTheme } = useApp();

  return (
    <div className="flex min-h-screen flex-col bg-paper">
      <header className="sticky top-0 z-40 border-b border-line bg-paper">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-baseline gap-2">
            <span className="text-h2 text-ink">سَنَد</span>
            <span className="text-caption text-muted">SANAD</span>
          </div>
          <div className="flex items-center gap-2 text-label">
            <button
              type="button"
              onClick={toggleLocale}
              className="rounded-chip border border-line bg-surface px-3 py-2 text-caption text-ink hover:border-orange"
            >
              {dict.common.toggleLang}
            </button>
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={dict.common.toggleTheme}
              className="rounded-chip border border-line bg-surface px-3 py-2 text-caption text-ink hover:border-orange"
            >
              ◑
            </button>
            <Link
              href="/login"
              className="rounded-chip bg-orange px-4 py-2 text-caption text-white"
            >
              {dict.login.submit}
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-reading flex-1 flex-col justify-center px-6 py-16">
        <p className="text-label text-orange-ink">{dict.tagline}</p>
        <h1 className="mt-4 text-display text-ink" style={{ fontSize: "3.5rem", lineHeight: 1.15 }}>
          سَنَد
        </h1>
        <p className="mt-6 max-w-prose text-body text-ink">
          يكشف المخالفة التنظيمية أو الشرعية في العقد، مع مصدرها النظامي الدقيق، قبل التوقيع.
          كل ملاحظة مرتبطة بنصها المصدري. لا مصدر، لا ادعاء.
        </p>

        <div dir="ltr" className="mt-8 border-t border-line pt-6">
          <p className="text-label text-ink">Sovereign AI compliance for Saudi organizations.</p>
          <p className="mt-2 text-body text-muted">
            Every finding is bound to the exact article it cites. Zero Unsourced Findings.
          </p>
        </div>

        <nav className="mt-12 flex flex-wrap gap-3">
          <Link href="/contracts" className="rounded-chip bg-orange px-6 py-3 text-label text-white">
            {dict.nav.contracts}
          </Link>
          <Link
            href="/idea-check"
            className="rounded-chip border border-line bg-surface px-6 py-3 text-label text-ink hover:border-orange"
          >
            {dict.nav.ideaCheck}
          </Link>
          <Link
            href="/join"
            className="rounded-chip px-6 py-3 text-label text-orange-ink hover:text-orange"
          >
            {dict.join.title}
          </Link>
        </nav>
      </main>
    </div>
  );
}
