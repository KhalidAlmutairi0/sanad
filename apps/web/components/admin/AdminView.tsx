"use client";

import { useEffect, useState } from "react";
import { AppLayout, Button, MonoChip } from "@/components/design/Shared";
import { apiGet, apiPost, apiPut } from "@/lib/api";
import type { AuditItem, CorpusItem, Invite, Prompts, Role } from "@/types";

const ROLE_AR: Record<string, string> = { reviewer: "مراجع", sharia_board: "هيئة شرعية", admin: "مشرف" };

function Card({ title, hint, children, wide = false }: { title: string; hint?: string; children: React.ReactNode; wide?: boolean }) {
  return (
    <section className={`bg-card border border-border rounded-xl p-6 ${wide ? "lg:col-span-2" : ""}`}>
      <h2 className="text-lg font-bold">{title}</h2>
      {hint && <p className="mt-1 text-[13px] text-muted-foreground">{hint}</p>}
      {children}
    </section>
  );
}

export function AdminView() {
  const [domains, setDomains] = useState("");
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
      .catch((e) => { if ((e as Error & { code?: string }).code === "forbidden") setForbidden(true); })
      .finally(() => setLoading(false));
  }, []);

  async function save() {
    setSaved(false);
    const list = domains.split("\n").map((d) => d.trim()).filter(Boolean);
    await apiPut("/admin/allowlist", { domains: list }).catch(() => null);
    setSaved(true);
  }

  async function generateInvite() {
    const created = await apiPost<Invite>("/admin/invites", { role: inviteRole, email: inviteEmail.trim() || null }).catch(() => null);
    if (created) { setInvites((prev) => [created, ...prev]); setInviteEmail(""); }
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
    if (updated) { setPrompts(updated); setPromptsSaved(true); setTimeout(() => setPromptsSaved(false), 2500); }
  }

  const inputCls = "rounded-md border border-border bg-background px-3 py-2 text-[14px] outline-none focus:border-primary";

  if (forbidden) {
    return (
      <AppLayout>
        <div className="max-w-[700px] mx-auto py-16">
          <p className="rounded-xl border border-border bg-card p-8 text-[15px] text-muted-foreground text-center">
            هذه الصفحة للمشرفين فقط. سجّل الدخول بحساب مشرف.
          </p>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="space-y-8">
        <div className="border-b border-border pb-6">
          <h1 className="text-2xl font-bold mb-1">الإدارة</h1>
          <p className="text-[13px] text-muted-foreground font-mono">ADMIN CONSOLE</p>
        </div>

        {loading ? (
          <p className="py-16 text-center text-muted-foreground">جاري التحميل…</p>
        ) : (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {corpus.length > 0 && (
              <Card title="مخزون الأنظمة" wide>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-[13px] text-muted-foreground font-mono">{corpus.reduce((s, c) => s + c.articles, 0)} مادة</span>
                </div>
                <div className="mt-4 max-h-[40vh] overflow-auto rounded-lg border border-border">
                  <table className="w-full text-[14px] text-right">
                    <thead className="bg-background/50 border-b border-border text-muted-foreground text-[13px] sticky top-0">
                      <tr>
                        <th className="px-3 py-2 font-normal">النظام</th>
                        <th className="px-3 py-2 font-normal">الجهة</th>
                        <th className="px-3 py-2 font-normal text-left">المواد</th>
                        <th className="px-3 py-2 font-normal text-left">آخر مطابقة</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {corpus.map((c) => (
                        <tr key={c.code}>
                          <td className="px-3 py-2">{c.name_ar}</td>
                          <td className="px-3 py-2 text-muted-foreground">{c.authority}</td>
                          <td className="px-3 py-2 text-left font-mono tnum">
                            {c.articles}
                            {c.official_fetch > 0 && <span className="ms-2 text-[11px] text-primary">AUTO</span>}
                          </td>
                          <td className="px-3 py-2 text-left text-[13px] text-muted-foreground font-mono">{c.last_reconciled_at ? c.last_reconciled_at.slice(0, 10) : "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}

            {prompts && (
              <Card title="توجيهات النماذج" hint="نص إرشادي إضافي يُضاف إلى تعليمات التحليل. العقد الأساسي مقفل ولا يُعدّل." wide>
                <div className="mt-4 grid grid-cols-1 gap-6 md:grid-cols-2">
                  <div>
                    <label className="text-[14px] font-medium">توجيه اختبار العقود</label>
                    <textarea value={prompts.contracts_guidance} onChange={(e) => setPrompts({ ...prompts, contracts_guidance: e.target.value })} rows={6}
                      className={`mt-2 w-full ${inputCls}`} dir="rtl" />
                    {prompts.contracts_contract && (
                      <details className="mt-2">
                        <summary className="cursor-pointer text-[13px] text-muted-foreground">العقد المقفل</summary>
                        <p dir="ltr" className="mt-2 rounded-md bg-background p-3 text-[12px] text-muted-foreground font-mono">{prompts.contracts_contract}</p>
                      </details>
                    )}
                  </div>
                  <div>
                    <label className="text-[14px] font-medium">توجيه فحص الفكرة</label>
                    <textarea value={prompts.idea_guidance} onChange={(e) => setPrompts({ ...prompts, idea_guidance: e.target.value })} rows={6}
                      className={`mt-2 w-full ${inputCls}`} dir="rtl" />
                    {prompts.idea_contract && (
                      <details className="mt-2">
                        <summary className="cursor-pointer text-[13px] text-muted-foreground">العقد المقفل</summary>
                        <p dir="ltr" className="mt-2 rounded-md bg-background p-3 text-[12px] text-muted-foreground font-mono">{prompts.idea_contract}</p>
                      </details>
                    )}
                  </div>
                </div>
                <div className="mt-4 flex items-center gap-3">
                  <Button onClick={savePrompts} className="h-9 px-5 text-[14px]">حفظ</Button>
                  {promptsSaved && <span className="text-[14px] text-primary">تم الحفظ</span>}
                </div>
              </Card>
            )}

            <Card title="النطاقات المسموح بها" hint="نطاقات البريد المسموح لها بالتسجيل، نطاق في كل سطر.">
              <textarea value={domains} onChange={(e) => setDomains(e.target.value)} rows={8} dir="ltr"
                className={`mt-4 w-full font-mono ${inputCls}`} />
              <div className="mt-3 flex items-center gap-3">
                <Button onClick={save} className="h-9 px-5 text-[14px]">حفظ</Button>
                {saved && <span className="text-[14px] text-primary">تم الحفظ</span>}
              </div>
            </Card>

            <Card title="دعوات المستخدمين" hint="أنشئ رمز دعوة لعضو جديد وحدد صلاحيته.">
              <div className="mt-4 flex flex-wrap items-end gap-3">
                <label className="flex flex-col gap-1">
                  <span className="text-[13px] text-muted-foreground">الصلاحية</span>
                  <select value={inviteRole} onChange={(e) => setInviteRole(e.target.value as Role)} className={inputCls}>
                    <option value="reviewer">مراجع</option>
                    <option value="sharia_board">هيئة شرعية</option>
                    <option value="admin">مشرف</option>
                  </select>
                </label>
                <label className="flex min-w-[12rem] flex-1 flex-col gap-1">
                  <span className="text-[13px] text-muted-foreground">البريد (اختياري)</span>
                  <input type="email" dir="ltr" value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} className={inputCls} />
                </label>
                <Button onClick={generateInvite} className="h-10 px-5 text-[14px]">إنشاء</Button>
              </div>
              <div className="mt-4 max-h-[40vh] overflow-y-auto">
                {invites.map((inv) => (
                  <div key={inv.code} className="flex items-center justify-between gap-4 border-b border-border py-3 last:border-0">
                    <div className="min-w-0">
                      <code dir="ltr" className="text-[14px] font-mono">{inv.code}</code>
                      <p className="truncate text-[13px] text-muted-foreground">{ROLE_AR[inv.role] ?? inv.role}{inv.email ? ` · ${inv.email}` : ""}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`text-[13px] ${inv.used ? "text-muted-foreground" : "text-primary"}`}>{inv.used ? "مُستخدم" : "متاح"}</span>
                      {!inv.used && (
                        <button onClick={() => copyCode(inv.code)} className="rounded-md border border-border px-3 py-1 text-[13px] hover:bg-border transition-colors">
                          {copied === inv.code ? "نُسخ" : "نسخ"}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card title="سجل التدقيق">
              <div className="mt-4 max-h-[60vh] overflow-y-auto">
                {audit.map((a, i) => (
                  <div key={i} className="flex items-center justify-between gap-4 border-b border-border py-3 last:border-0">
                    <div className="min-w-0">
                      <p className="truncate text-[14px]">{a.action}</p>
                      <p className="truncate text-[13px] text-muted-foreground">{a.target ?? ""}</p>
                    </div>
                    <span className={`text-[13px] font-mono ${a.verdict === "denied" ? "text-destructive" : a.verdict === "allowed" ? "text-primary" : "text-muted-foreground"}`}>{a.verdict}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
