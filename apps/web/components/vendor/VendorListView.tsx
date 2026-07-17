"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppLayout, Button, MonoChip } from "@/components/design/Shared";
import { apiGet } from "@/lib/api";
import type { VendorEvaluationListItem } from "@/types";

const STATUS_AR: Record<string, string> = { uploading: "قيد الرفع", comparing: "قيد التقييم", done: "اكتملت" };

export function VendorListView() {
  const [items, setItems] = useState<VendorEvaluationListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<{ items: VendorEvaluationListItem[] }>("/vendor-evaluations")
      .then((d) => setItems(d.items)).finally(() => setLoading(false));
  }, []);

  return (
    <AppLayout>
      <div className="max-w-[900px] mx-auto space-y-6">
        <div className="flex items-center justify-between border-b border-border pb-6">
          <div>
            <h1 className="text-2xl font-bold mb-1">تقييم الموردين</h1>
            <p className="text-[13px] text-muted-foreground">مقارنة عروض موردين متعددين لطلب عروض واحد.</p>
          </div>
          <Link href="/vendors/new"><Button>تقييم جديد</Button></Link>
        </div>

        <div className="bg-card border border-border rounded-xl overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-muted-foreground">جاري التحميل…</div>
          ) : items.length === 0 ? (
            <div className="p-12 text-center text-muted-foreground">ما فيه تقييمات بعد. ابدأ تقييماً جديداً.</div>
          ) : (
            <div className="divide-y divide-border">
              {items.map((ev) => (
                <Link key={ev.id} href={`/vendors/${ev.id}`}
                  className="p-4 flex items-center justify-between hover:bg-background/50 transition-colors">
                  <div>
                    <h3 className="font-medium text-[15px] mb-1">{ev.title}</h3>
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-[11px] text-muted-foreground">{ev.created_at?.slice(0, 10)}</span>
                      <MonoChip className="text-muted-foreground">{ev.vendor_count} مورد</MonoChip>
                    </div>
                  </div>
                  <span className={`text-[12px] px-2 py-0.5 rounded border ${ev.status === "done" ? "border-primary text-primary" : "border-[#B4842F] text-[#B4842F]"}`}>
                    {STATUS_AR[ev.status] ?? ev.status}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
