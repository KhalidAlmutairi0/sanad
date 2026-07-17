"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useApp } from "@/lib/i18n";
import { login, guestLogin } from "@/lib/api";
import { Button } from "@/components/design/Shared";

export function LoginForm() {
  const { toggleLocale, locale } = useApp();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
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

  async function enterAsGuest() {
    setBusy(true);
    setError(false);
    try {
      await guestLogin();
      router.push("/contracts");
      router.refresh();
    } catch {
      setError(true);
      setBusy(false);
    }
  }

  return (
    <div className="min-h-[100dvh] flex flex-col items-center justify-center bg-background relative overflow-hidden p-6">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-[100px] pointer-events-none" />
      <div className="w-full max-w-[420px] bg-card border border-border rounded-xl p-8 shadow-2xl relative z-10">
        <div className="flex justify-between items-start mb-10">
          <Link href="/" className="flex flex-col">
            <span className="font-bold text-2xl leading-none">سند</span>
            <span className="font-mono text-xs text-muted-foreground leading-none mt-1">SANAD</span>
          </Link>
          <button onClick={toggleLocale} className="text-[13px] font-medium text-muted-foreground hover:text-foreground transition-colors border border-border px-2 py-1 rounded">
            {locale === "ar" ? "EN" : "ع"}
          </button>
        </div>
        <form onSubmit={submit} className="space-y-5">
          <div className="space-y-2">
            <label className="text-[13px] font-medium text-muted-foreground block">البريد الإلكتروني المؤسسي</label>
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-background border border-border rounded-md px-4 py-2.5 text-[15px] outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all text-left font-mono"
              dir="ltr" placeholder="name@bank.sa" />
          </div>
          <div className="space-y-2">
            <label className="text-[13px] font-medium text-muted-foreground block">كلمة المرور</label>
            <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-background border border-border rounded-md px-4 py-2.5 text-[15px] outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all text-left font-mono"
              dir="ltr" placeholder="••••••••" />
          </div>
          {error && <p className="text-[13px] text-destructive">بيانات الدخول غير صحيحة</p>}
          <Button type="submit" disabled={busy} className="w-full mt-2">{busy ? "جارٍ الدخول…" : "تسجيل الدخول"}</Button>
        </form>
        <button onClick={enterAsGuest} disabled={busy}
          className="w-full mt-3 text-[14px] font-medium text-primary hover:underline disabled:opacity-50">
          الدخول كضيف للتجربة
        </button>
        <div className="mt-8 pt-6 border-t border-border text-center text-[15px]">
          <span className="text-muted-foreground">ليس لديك حساب؟ </span>
          <Link href="/join" className="text-primary hover:underline font-medium">إنشاء حساب بدعوة</Link>
        </div>
      </div>
    </div>
  );
}
