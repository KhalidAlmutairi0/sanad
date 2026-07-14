import Link from "next/link";
import { redirect } from "next/navigation";
import { serverGet, ApiRequestError } from "@/lib/server-api";
import { AppLayout } from "@/components/design/Shared";
import { UploadContract } from "@/components/contracts/UploadContract";
import type { ContractListItem } from "@/types";

interface ContractList {
  items: ContractListItem[];
  total: number;
}

const STATUS_AR: Record<string, string> = {
  uploaded: "مرفوع",
  sanitizing: "جاري الفحص",
  sanitized: "تم الفحص",
  extracting: "جاري الاستخراج",
  reviewing: "قيد المراجعة",
  reviewed: "تمت المراجعة",
  failed: "فشل",
};

function statusClass(status: string): string {
  if (status === "reviewed") return "border-primary text-primary";
  if (status === "failed") return "border-destructive text-destructive";
  if (status === "uploaded") return "border-muted-foreground text-muted-foreground";
  return "border-[#D4812A] text-[#D4812A]";
}

export default async function ContractsPage() {
  let data: ContractList;
  try {
    data = await serverGet<ContractList>("/contracts");
  } catch (e) {
    if (e instanceof ApiRequestError && e.status === 401) redirect("/login");
    throw e;
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between border-b border-border pb-6">
          <h1 className="text-2xl font-bold">العقود</h1>
          <UploadContract />
        </div>

        <div className="bg-card border border-border rounded-xl overflow-hidden">
          {data.items.length > 0 ? (
            <div className="divide-y divide-border">
              {data.items.map((c) => (
                <Link key={c.id} href={`/contracts/${c.id}`}
                  className="p-4 flex items-center justify-between hover:bg-background/50 cursor-pointer transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded bg-background border border-border flex items-center justify-center text-muted-foreground shrink-0">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /></svg>
                    </div>
                    <div>
                      <h3 className="font-medium text-[15px] mb-1">{c.title}</h3>
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-[11px] text-muted-foreground tnum">{c.created_at?.slice(0, 10)}</span>
                        <span className={`text-[11px] px-2 py-0.5 rounded border ${statusClass(c.status)}`}>
                          {STATUS_AR[c.status] ?? c.status}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {c.readiness_score !== null ? (
                      <div className="flex items-center gap-2">
                        <span className="text-[13px] text-muted-foreground">الجاهزية</span>
                        <span className={`font-mono text-[15px] font-bold tnum px-2 py-1 border rounded-md ${c.readiness_score >= 80 ? "text-primary border-primary" : "text-[#D4812A] border-[#D4812A]"}`}>
                          {c.readiness_score}
                        </span>
                      </div>
                    ) : (
                      <span className="text-[13px] text-muted-foreground">—</span>
                    )}
                    <div className="text-muted-foreground">←</div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="p-12 text-center text-muted-foreground">ما عندك عقود حتى الآن. ارفع عقد وابدأ المراجعة.</div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
