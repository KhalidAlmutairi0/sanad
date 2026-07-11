"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/ui/Header";
import { useApp } from "@/lib/i18n";
import { apiGet, apiPost } from "@/lib/api";
import { DEMO_ALLOWLIST, DEMO_AUDIT } from "@/lib/demo";
import type { AuditItem } from "@/types";

export function AdminView({ demo = false }: { demo?: boolean }) {
  const { dict } = useApp();
  const [domains, setDomains] = useState<string>(demo ? DEMO_ALLOWLIST.join("\n") : "");
  const [audit, setAudit] = useState<AuditItem[]>(demo ? DEMO_AUDIT : []);
  const [forbidden, setForbidden] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(!demo);

  useEffect(() => {
    if (demo) return;
    Promise.all([
      apiGet<{ domains: string[] }>("/admin/allowlist").then((d) => setDomains(d.domains.join("\n"))),
      apiGet<{ items: AuditItem[] }>("/admin/audit?limit=25").then((d) => setAudit(d.items)),
    ])
      .catch((e) => {
        if ((e as Error & { code?: string }).code === "forbidden") setForbidden(true);
      })
      .finally(() => setLoading(false));
  }, [demo]);

  async function save() {
    setSaved(false);
    const list = domains.split("\n").map((d) => d.trim()).filter(Boolean);
    if (!demo) await apiPost("/admin/allowlist", { domains: list }).catch(() => null);
    setSaved(true);
  }

  if (forbidden) {
    return (
      <div className="min-h-screen">
        <Header />
        <main className="mx-auto max-w-reading px-6 py-12">
          <p className="rounded-card border border-line bg-surface p-8 text-body text-muted">
            هذه الصفحة للمشرفين فقط. سجّل الدخول بحساب مشرف.
          </p>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-6xl px-6 py-12">
        <h1 className="text-h1 font-semibold text-ink">{dict.admin.title}</h1>
        {loading ? (
          <p className="mt-8 text-body text-muted">{dict.common.loading}</p>
        ) : (
          <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-2">
            <section className="rounded-card border border-line bg-surface p-6">
              <h2 className="text-h3 text-ink">{dict.admin.allowlist}</h2>
              <p className="mt-1 text-caption text-muted">{dict.admin.allowlistHint}</p>
              <textarea
                value={domains}
                onChange={(e) => setDomains(e.target.value)}
                rows={8}
                dir="ltr"
                className="mt-4 w-full rounded-chip border border-line bg-paper p-3 text-label text-ink"
                style={{ fontFamily: "var(--font-plex-mono)" }}
              />
              <div className="mt-3 flex items-center gap-3">
                <button onClick={save} className="rounded-chip bg-orange px-6 py-2 text-label text-white">
                  {dict.admin.save}
                </button>
                {saved && <span className="text-label text-severity-ok">{dict.admin.saved}</span>}
              </div>
            </section>

            <section className="rounded-card border border-line bg-surface p-6">
              <h2 className="text-h3 text-ink">{dict.admin.audit}</h2>
              <div className="mt-4 max-h-[60vh] overflow-y-auto">
                {audit.map((a, i) => (
                  <div key={i} className="flex items-center justify-between gap-4 border-b border-line py-3 last:border-0">
                    <div className="min-w-0">
                      <p className="truncate text-label text-ink">{a.action}</p>
                      <p className="truncate text-caption text-muted">{a.target ?? ""}</p>
                    </div>
                    <span
                      className={`text-label ${
                        a.verdict === "denied" ? "text-severity-critical" : a.verdict === "allowed" ? "text-severity-ok" : "text-muted"
                      }`}
                    >
                      {a.verdict}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
