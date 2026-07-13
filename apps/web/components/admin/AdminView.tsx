"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/ui/Header";
import { useApp } from "@/lib/i18n";
import { apiGet, apiPost, apiPut } from "@/lib/api";
import type { AuditItem, CorpusItem, Invite, Prompts, Role } from "@/types";

export function AdminView() {
  const { dict } = useApp();
  const [domains, setDomains] = useState<string>("");
  const [audit, setAudit] = useState<AuditItem[]>([]);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [corpus, setCorpus] = useState<CorpusItem[]>([]);
  const [inviteRole, setInviteRole] = useState<Role>("reviewer");
  const [inviteEmail, setInviteEmail] = useState("");
  const [copied, setCopied] = useState<string | null>(null);
  const [prompts, setPrompts] = useState<Prompts | null>(null);
  const [promptsSaved, setPromptsSaved] = useState(false);
  const [forbidden, setForbidden] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiGet<{ domains: string[] }>("/admin/allowlist").then((d) => setDomains(d.domains.join("\n"))),
      apiGet<{ items: AuditItem[] }>("/admin/audit?limit=25").then((d) => setAudit(d.items)),
      apiGet<{ items: Invite[] }>("/admin/invites").then((d) => setInvites(d.items)).catch(() => null),
      apiGet<Prompts>("/admin/prompts").then((d) => setPrompts(d)).catch(() => null),
      apiGet<{ items: CorpusItem[] }>("/admin/corpus").then((d) => setCorpus(d.items)).catch(() => null),
    ])
      .catch((e) => {
        if ((e as Error & { code?: string }).code === "forbidden") setForbidden(true);
      })
      .finally(() => setLoading(false));
  }, []);

  async function save() {
    setSaved(false);
    const list = domains.split("\n").map((d) => d.trim()).filter(Boolean);
    await apiPut("/admin/allowlist", { domains: list }).catch(() => null);
    setSaved(true);
  }

  async function generateInvite() {
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

  async function savePrompts() {
    if (!prompts) return;
    setPromptsSaved(false);
    const updated = await apiPost<Prompts>("/admin/prompts", {
      contracts_guidance: prompts.contracts_guidance,
      idea_guidance: prompts.idea_guidance,
    }).catch(() => null);
    if (updated) {
      setPrompts(updated);
      setPromptsSaved(true);
      setTimeout(() => setPromptsSaved(false), 2500);
    }
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
            {corpus.length > 0 && (
              <section className="rounded-card border border-line bg-surface p-6 lg:col-span-2">
                <div className="flex items-baseline justify-between">
                  <h2 className="text-h3 text-ink">{dict.admin.corpus}</h2>
                  <span className="text-caption text-muted">
                    {corpus.reduce((s, c) => s + c.articles, 0)} {dict.admin.articles}
                  </span>
                </div>
                <div className="mt-4 max-h-[40vh] overflow-auto">
                  <table className="w-full text-label">
                    <thead>
                      <tr className="border-b border-line text-caption text-muted">
                        <th className="px-3 py-2 text-start font-medium">{dict.admin.regulation}</th>
                        <th className="px-3 py-2 text-start font-medium">{dict.admin.authority}</th>
                        <th className="px-3 py-2 text-end font-medium">{dict.admin.articles}</th>
                        <th className="px-3 py-2 text-end font-medium">{dict.admin.reconciled}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {corpus.map((c) => (
                        <tr key={c.code} className="border-b border-line last:border-0">
                          <td className="px-3 py-2 text-ink">{c.name_ar}</td>
                          <td className="px-3 py-2 text-caption text-muted">{c.authority}</td>
                          <td className="px-3 py-2 text-end tabular text-ink" style={{ fontFamily: "var(--font-plex-mono)" }}>
                            {c.articles}
                            {c.official_fetch > 0 && (
                              <span className="ms-2 text-caption text-orange-ink">{dict.admin.autoTag}</span>
                            )}
                          </td>
                          <td className="px-3 py-2 text-end text-caption text-muted">
                            {c.last_reconciled_at ? c.last_reconciled_at.slice(0, 10) : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}
            {prompts && (
              <section className="rounded-card border border-line bg-surface p-6 lg:col-span-2">
                <h2 className="text-h3 text-ink">{dict.admin.prompts}</h2>
                <p className="mt-1 text-caption text-muted">{dict.admin.promptsHint}</p>
                <div className="mt-4 grid grid-cols-1 gap-6 md:grid-cols-2">
                  <div>
                    <label className="text-label text-ink">{dict.admin.contractsGuidance}</label>
                    <textarea
                      value={prompts.contracts_guidance}
                      onChange={(e) => setPrompts({ ...prompts, contracts_guidance: e.target.value })}
                      rows={6}
                      className="mt-2 w-full rounded-chip border border-line bg-paper p-3 text-body text-ink"
                    />
                    {prompts.contracts_contract && (
                      <details className="mt-2">
                        <summary className="cursor-pointer text-caption text-muted">{dict.admin.lockedContract}</summary>
                        <p dir="ltr" className="mt-2 rounded-chip bg-orange-bg p-3 text-caption text-orange-ink">
                          {prompts.contracts_contract}
                        </p>
                      </details>
                    )}
                  </div>
                  <div>
                    <label className="text-label text-ink">{dict.admin.ideaGuidance}</label>
                    <textarea
                      value={prompts.idea_guidance}
                      onChange={(e) => setPrompts({ ...prompts, idea_guidance: e.target.value })}
                      rows={6}
                      className="mt-2 w-full rounded-chip border border-line bg-paper p-3 text-body text-ink"
                    />
                    {prompts.idea_contract && (
                      <details className="mt-2">
                        <summary className="cursor-pointer text-caption text-muted">{dict.admin.lockedContract}</summary>
                        <p dir="ltr" className="mt-2 rounded-chip bg-orange-bg p-3 text-caption text-orange-ink">
                          {prompts.idea_contract}
                        </p>
                      </details>
                    )}
                  </div>
                </div>
                <div className="mt-4 flex items-center gap-3">
                  <button onClick={savePrompts} className="rounded-chip bg-orange px-6 py-2 text-label text-white">
                    {dict.admin.save}
                  </button>
                  {promptsSaved && <span className="text-label text-severity-ok">{dict.admin.promptsSaved}</span>}
                </div>
              </section>
            )}
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
