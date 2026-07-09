"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useApp } from "@/lib/i18n";
import { login } from "@/lib/api";

export function LoginForm({ demo = false }: { demo?: boolean }) {
  const { dict, toggleLocale } = useApp();
  const router = useRouter();
  const [email, setEmail] = useState("reviewer@sanad.local");
  const [password, setPassword] = useState(demo ? "demo" : "");
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    // Demo mode: no backend — go straight to the screens.
    if (demo) {
      router.push("/contracts");
      return;
    }
    setBusy(true);
    setError(false);
    try {
      await login(email, password);
      router.push("/contracts");
      router.refresh();
    } catch {
      setError(true);
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-reading flex-col justify-center px-6">
      <div className="mx-auto w-full max-w-sm">
        <p className="text-label text-orange-ink">{dict.tagline}</p>
        <h1 className="mt-2 text-display font-bold">سَنَد</h1>
        {demo && (
          <p className="mt-2 rounded-chip bg-orange-bg px-3 py-1 text-caption text-orange-ink">
            وضع العرض — بيانات توضيحية فقط · Demo mode — sample data only
          </p>
        )}
        <form onSubmit={submit} className="mt-8 space-y-4">
          <label className="block">
            <span className="text-label text-muted">{dict.login.email}</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-chip border border-line bg-surface px-4 py-3 text-body text-ink"
              required
              dir="ltr"
            />
          </label>
          <label className="block">
            <span className="text-label text-muted">{dict.login.password}</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-chip border border-line bg-surface px-4 py-3 text-body text-ink"
              required={!demo}
              dir="ltr"
            />
          </label>
          {error && <p className="text-label text-severity-critical">{dict.login.error}</p>}
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-chip bg-orange px-6 py-3 text-label text-white disabled:opacity-50"
          >
            {demo ? "دخول العرض · Enter demo" : dict.login.submit}
          </button>
        </form>
        <button type="button" onClick={toggleLocale} className="mt-6 text-label text-muted">
          {dict.common.toggleLang}
        </button>
      </div>
    </main>
  );
}
