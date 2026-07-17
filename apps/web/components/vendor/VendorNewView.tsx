"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AppLayout, Button, MonoChip } from "@/components/design/Shared";
import { apiPost } from "@/lib/api";

interface Row {
  file: File | null;
  vendorName: string;
}

export function VendorNewView() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [rows, setRows] = useState<Row[]>([{ file: null, vendorName: "" }, { file: null, vendorName: "" }]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<string | null>(null);

  const labeled = rows.filter((r) => r.file && r.vendorName.trim());
  const canRun = title.trim() && labeled.length >= 1 && !busy;

  function setRow(i: number, patch: Partial<Row>) {
    setRows((rs) => rs.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  }

  async function runComparison() {
    setBusy(true);
    setError(null);
    try {
      const ev = await apiPost<{ id: string }>("/vendor-evaluations", { title });
      let n = 0;
      for (const r of labeled) {
        setProgress(`رفع ${++n} من ${labeled.length}…`);
        const sub = await apiPost<{ id: string; upload_url: string }>(
          `/vendor-evaluations/${ev.id}/submissions`,
          { vendor_name: r.vendorName.trim(), filename: r.file!.name },
        );
        const put = await fetch(sub.upload_url, { method: "PUT", body: r.file! });
        if (!put.ok) throw new Error("upload_failed");
      }
      setProgress("بدء المقارنة…");
      await apiPost(`/vendor-evaluations/${ev.id}/run-comparison`);
      router.push(`/vendors/${ev.id}`);
    } catch (e) {
      setError((e as Error & { code?: string }).code ?? "فشل تشغيل المقارنة");
      setBusy(false);
    }
  }

  return (
    <AppLayout>
      <div className="max-w-[800px] mx-auto space-y-8">
        <div className="border-b border-border pb-6">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold">تقييم الموردين</h1>
            <MonoChip className="text-primary border-primary/40">RFP</MonoChip>
          </div>
          <p className="text-[15px] text-muted-foreground">
            ارفع عروض عدة موردين لطلب عروض واحد، وسمِّ كل ملف باسم المورد، ثم شغّل المقارنة. هذا مسار مستقل عن مراجعة عقد واحد.
          </p>
        </div>

        <label className="block">
          <span className="text-[13px] text-muted-foreground">عنوان طلب العروض</span>
          <input value={title} onChange={(e) => setTitle(e.target.value)} disabled={busy}
            placeholder="مثال: خدمات سحابية للأفراد — RFP 2026"
            className="mt-1 w-full bg-card border border-border rounded-lg px-4 py-2.5 text-[15px] outline-none focus:border-primary" />
        </label>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-[15px] font-bold">عروض الموردين</h2>
            <button onClick={() => setRows((rs) => [...rs, { file: null, vendorName: "" }])} disabled={busy}
              className="text-[13px] text-primary hover:underline">+ إضافة مورد</button>
          </div>
          {rows.map((r, i) => (
            <div key={i} className="bg-card border border-border rounded-xl p-4 flex flex-col sm:flex-row gap-3 sm:items-center">
              <input value={r.vendorName} onChange={(e) => setRow(i, { vendorName: e.target.value })} disabled={busy}
                placeholder={`اسم المورد ${i + 1}`}
                className="sm:w-1/3 bg-background border border-border rounded-md px-3 py-2 text-[14px] outline-none focus:border-primary" />
              <input type="file" accept=".pdf,.docx,.txt" disabled={busy}
                onChange={(e) => setRow(i, { file: e.target.files?.[0] ?? null })}
                className="flex-1 text-[13px] text-muted-foreground file:me-3 file:rounded-md file:border-0 file:bg-primary/10 file:text-primary file:px-3 file:py-1.5" />
              {rows.length > 2 && !busy && (
                <button onClick={() => setRows((rs) => rs.filter((_, j) => j !== i))}
                  className="text-[13px] text-muted-foreground hover:text-destructive">حذف</button>
              )}
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between border-t border-border pt-6">
          <span className="text-[13px] text-muted-foreground">
            {labeled.length} مورد جاهز — لن تُشغَّل المقارنة تلقائياً؛ اضغط الزر لتأكيد اكتمال الدفعة.
          </span>
          <Button onClick={runComparison} disabled={!canRun}>{busy ? (progress ?? "…") : "تشغيل المقارنة"}</Button>
        </div>
        {error && <p className="text-[13px] text-destructive text-end">{error}</p>}
      </div>
    </AppLayout>
  );
}
