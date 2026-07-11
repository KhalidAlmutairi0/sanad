"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/ui/Header";
import { useApp } from "@/lib/i18n";
import { apiGet, apiPost } from "@/lib/api";
import { DEMO_ALLOWLIST, DEMO_AUDIT } from "@/lib/demo";
import type { AuditItem, Invite, Role } from "@/types";

export function AdminView({ demo = false }: { demo?: boolean }) {
  const { dict } = useApp();
  const [domains, setDomains] = useState<string>(demo ? DEMO_ALLOWLIST.join("\n") : "");
  const [audit, setAudit] = useState<AuditItem[]>(demo ? DEMO_AUDIT : []);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [inviteRole, setInviteRole] = useState<Role>("reviewer");
  const [inviteEmail, setInviteEmail] = useState("");
  const [copied, setCopied] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(!demo);

  useEffect(() => {
    if (demo) return;
    Promise.all([
      apiGet<{ domains: string[] }>("/admin/allowlist").then((d) => setDomains(d.domains.join("\n"))),
      apiGet<{ items: AuditItem[] }>("/admin/audit?limit=25").then((d) => setAudit(d.items)),
      apiGet<{ items: Invite[] }>("/admin/invites").then((d) => setInvites(d.items)).catch(() => null),
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

  async function generateInvite() {
    if (demo) return;
    const body = { role: inviteRole, email: inviteEmail.trim() || null };
    const created = await apiPost<Invite>("/admin/invites", body).catch(() => null);
    if (created) {
      setInvites((prev) => [created, ...prev]);
      setInviteEmail("");
    }
  }

  async function copyCode(code: string) {
    await navigator.clipboard.writeText(code).catch(() => null);
    setCopied(code);
    setTimeout(() => setCopied((c) => (c === code ? null : c)), 1500);
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
              <h2 className="text-h3 text-ink">{dict.admin.invites}</h2>
              <p className="mt-1 text-caption text-muted">{dict.admin.invitesHint}</p>
              <div className="mt-4 flex flex-wrap items-end gap-3">
                <label className="flex flex-col gap-1">
                  <span className="text-caption text-muted">{dict.admin.role}</span>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value as Role)}
                    className="rounded-chip border border-line bg-paper px-3 py-2 text-label text-ink"
                  >
                    <option value="reviewer">{dict.admin.roles.reviewer}</option>
                    <option value="sharia_board">{dict.admin.roles.sharia_board}</option>
                    <option value="admin">{dict.admin.roles.admin}</option>
                  </select>
                </label>
                <label className="flex min-w-[12rem] flex-1 flex-col gap-1">
                  <span className="text-caption text-muted">{dict.admin.emailOptional}</span>
                  <input
                    type="email"
                    dir="ltr"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="rounded-chip border border-line bg-paper px-3 py-2 text-label text-ink"
                  />
                </label>
                <button onClick={generateInvite} className="rounded-chip bg-orange px-6 py-2 text-label text-white">
                  {dict.admin.generate}
                </button>
              </div>
              <div className="mt-4 max-h-[40vh] overflow-y-auto">
                {invites.map((inv) => (
                  <div key={inv.code} className="flex items-center justify-between gap-4 border-b border-line py-3 last:border-0">
                    <div className="min-w-0">
                      <code dir="ltr" className="text-label text-ink" style={{ fontFamily: "var(--font-plex-mono)" }}>
                        {inv.code}
                      </code>
                      <p className="truncate text-caption text-muted">
                        {dict.admin.roles[inv.role as keyof typeof dict.admin.roles] ?? inv.role}
                        {inv.email ? ` · ${inv.email}` : ""}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`text-caption ${inv.used ? "text-muted" : "text-severity-ok"}`}>
                        {inv.used ? dict.admin.used : dict.admin.unused}
                      </span>
                      {!inv.used && (
                        <button onClick={() => copyCode(inv.code)} className="rounded-chip border border-line px-3 py-1 text-caption text-ink">
                          {copied === inv.code ? dict.admin.copied : dict.admin.copy}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
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
