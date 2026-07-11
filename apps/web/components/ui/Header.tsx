"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useApp } from "@/lib/i18n";
import { logout } from "@/lib/api";

export function Header() {
  const { dict, toggleLocale, toggleTheme } = useApp();
  const router = useRouter();

  async function doLogout() {
    await logout();
    router.push("/login");
    router.refresh();
  }

  return (
    <header className="border-b border-line bg-surface">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-8">
          <Link href="/contracts" className="text-h2 font-bold text-ink">
            سَنَد
          </Link>
          <nav className="flex flex-wrap items-center gap-x-6 gap-y-2 text-label">
            <Link href="/contracts" className="text-ink hover:text-orange-ink">
              {dict.nav.contracts}
            </Link>
            <Link href="/idea-check" className="text-ink hover:text-orange-ink">
              {dict.nav.ideaCheck}
            </Link>
            <Link href="/register" className="text-ink hover:text-orange-ink">
              {dict.nav.register}
            </Link>
            <Link href="/monitoring" className="text-ink hover:text-orange-ink">
              {dict.nav.monitoring}
            </Link>
            <Link href="/evidence" className="text-ink hover:text-orange-ink">
              {dict.nav.evidence}
            </Link>
            <Link href="/admin" className="text-ink hover:text-orange-ink">
              {dict.nav.admin}
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-4 text-label">
          <button type="button" onClick={toggleLocale} className="text-muted hover:text-ink">
            {dict.common.toggleLang}
          </button>
          <button type="button" onClick={toggleTheme} className="text-muted hover:text-ink" aria-label={dict.common.toggleTheme}>
            ◑
          </button>
          <button type="button" onClick={doLogout} className="text-muted hover:text-ink">
            {dict.nav.logout}
          </button>
        </div>
      </div>
    </header>
  );
}
