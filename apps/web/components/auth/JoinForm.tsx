"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { register } from "@/lib/api";
import { Button, MonoChip } from "@/components/design/Shared";

const areas = [
  { id: "contracts", label: "مراجعة العقود", desc: "ارفع العقود واستلم الملاحظات المصدرية", route: "/contracts" },
  { id: "idea", label: "فحص الفكرة", desc: "افحص امتثال المنتجات والأفكار قبل البناء", route: "/idea-check" },
  { id: "register", label: "سجل الالتزامات", desc: "كل التزام في مكان واحد مع مصدره", route: "/register" },
  { id: "evidence", label: "مخزن الأدلة", desc: "ابحث في الأنظمة والمواد النظامية", route: "/evidence" },
];

export function JoinForm() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submitStep1(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(false);
    try {
      await register(email, password, code.trim());
      setStep(2);
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-[100dvh] flex flex-col items-center justify-center bg-background relative overflow-hidden p-6">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[300px] bg-primary/6 rounded-full blur-[100px] pointer-events-none" />
      <div className="w-full max-w-[460px] relative z-10">
        <div className="flex items-center gap-3 mb-8 justify-center">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-[13px] font-bold ${step === 1 ? "bg-primary text-white" : "bg-primary/20 text-primary"}`}>{step === 1 ? "1" : "✓"}</div>
          <div className={`flex-1 h-px max-w-[60px] ${step === 2 ? "bg-primary" : "bg-border"}`} />
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-[13px] font-bold ${step === 2 ? "bg-primary text-white" : "bg-border text-muted-foreground"}`}>2</div>
        </div>

        {step === 1 ? (
          <div className="bg-card border border-border rounded-xl p-8 shadow-lg">
            <div className="flex flex-col mb-8">
              <Link href="/" className="flex flex-col">
                <span className="font-bold text-2xl leading-none">سند</span>
                <span className="font-mono text-[10px] text-muted-foreground leading-none mt-1">SANAD</span>
              </Link>
              <h1 className="text-xl font-bold mt-6 mb-1">إكمال التسجيل</h1>
              <p className="text-[14px] text-muted-foreground">أدخل رمز الدعوة المرسل إليك لإنشاء حسابك.</p>
            </div>
            <form onSubmit={submitStep1} className="space-y-5">
              <div className="space-y-2">
                <label className="text-[13px] font-medium text-muted-foreground flex items-center justify-between">
                  رمز الدعوة<MonoChip className="text-[11px] py-0 border-none opacity-50">REQUIRED</MonoChip>
                </label>
                <input type="text" required value={code} onChange={(e) => setCode(e.target.value)}
                  className="w-full bg-background border border-border rounded-md px-4 py-2.5 text-[15px] outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all text-center font-mono tracking-widest"
                  dir="ltr" placeholder="XXXXXX" />
              </div>
              <div className="space-y-2">
                <label className="text-[13px] font-medium text-muted-foreground block">البريد الإلكتروني المؤسسي</label>
                <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-background border border-border rounded-md px-4 py-2.5 text-[15px] outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all text-left font-mono"
                  dir="ltr" placeholder="name@bank.sa" />
              </div>
              <div className="space-y-2">
                <label className="text-[13px] font-medium text-muted-foreground block">كلمة المرور الجديدة</label>
                <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-background border border-border rounded-md px-4 py-2.5 text-[15px] outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all text-left font-mono"
                  dir="ltr" placeholder="••••••••" />
              </div>
              {error && <p className="text-[13px] text-destructive">تعذّر إنشاء الحساب، تأكد من الرمز</p>}
              <Button type="submit" disabled={busy} className="w-full mt-2">{busy ? "جارٍ الإنشاء…" : "التالي"}</Button>
            </form>
            <div className="mt-8 pt-6 border-t border-border text-center text-[14px]">
              <span className="text-muted-foreground">لديك حساب بالفعل؟ </span>
              <Link href="/login" className="text-primary hover:underline font-medium">تسجيل الدخول</Link>
            </div>
          </div>
        ) : (
          <div>
            <div className="text-center mb-8">
              <h1 className="text-xl font-bold mb-2">تم إنشاء حسابك</h1>
              <p className="text-[14px] text-muted-foreground">من أين تبي تبدأ؟</p>
            </div>
            <div className="grid grid-cols-1 gap-3">
              {areas.map((a) => (
                <button key={a.id} onClick={() => { router.push(a.route); router.refresh(); }}
                  className="w-full text-right p-5 rounded-xl border border-border bg-card hover:border-primary/40 hover:bg-primary/5 transition-all group">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-bold text-[16px] mb-1 group-hover:text-primary transition-colors">{a.label}</p>
                      <p className="text-[13px] text-muted-foreground">{a.desc}</p>
                    </div>
                    <div className="w-9 h-9 rounded-full border border-border flex items-center justify-center text-muted-foreground group-hover:border-primary group-hover:text-primary transition-all shrink-0 ms-4">→</div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
