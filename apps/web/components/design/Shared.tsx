"use client";

// Signature SANAD design components, ported from the sanadscreen design (wouter → next/link).
import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { logout } from "@/lib/api";

export function MonoChip({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={`font-mono text-[13px] tnum px-2 py-1 border border-border rounded-md ${className}`}>
      {children}
    </span>
  );
}

export function SourceChip({ text, withLine = false, lineDirection = "right" }: {
  text: string; withLine?: boolean; lineDirection?: "right" | "left" | "top" | "bottom";
}) {
  return (
    <div className="relative inline-flex items-center">
      {withLine && (
        <svg
          className="absolute text-primary dash-draw"
          style={{
            [lineDirection === "right" ? "left" : "right"]: "100%",
            top: "50%", transform: "translateY(-50%)", width: "24px", height: "2px",
          }}
          viewBox="0 0 24 2" fill="none"
        >
          <path d="M0 1L24 1" stroke="currentColor" strokeWidth="2" />
        </svg>
      )}
      <span className="font-sans text-[13px] font-medium text-foreground bg-card px-3 py-1 border border-border rounded-md relative z-10">
        {text}
      </span>
    </div>
  );
}

export function FindingCard({ id, severity, text, source, showActions = false, className = "", onAccept, onReject }: {
  id: string; severity: "red" | "amber" | "muted"; text: React.ReactNode; source: string;
  showActions?: boolean; className?: string; onAccept?: () => void; onReject?: () => void;
}) {
  const sevColor = severity === "red" ? "bg-destructive" : severity === "amber" ? "bg-[#D4812A]" : "bg-muted-foreground";
  return (
    <div className={`bg-card border border-border rounded-[10px] p-5 flex flex-col gap-4 relative overflow-hidden ${className}`}>
      <div className="flex items-center gap-3">
        <div className={`w-2.5 h-2.5 rounded-full ${sevColor}`} />
        <MonoChip className="text-muted-foreground">{id}</MonoChip>
      </div>
      <p className="text-[17px] leading-[1.8] text-foreground">{text}</p>
      <div className="mt-2 flex items-center justify-between">
        <div className="flex items-center gap-4"><SourceChip text={source} withLine /></div>
        {showActions && (
          <div className="flex items-center gap-2">
            <button onClick={onReject} className="text-[13px] px-3 py-1.5 rounded-md border border-border hover:bg-border transition-colors">رفض</button>
            <button onClick={onAccept} className="text-[13px] px-3 py-1.5 rounded-md bg-primary text-primary-foreground font-medium hover:opacity-90 transition-opacity">تطبيق</button>
          </div>
        )}
      </div>
    </div>
  );
}

export function ReadinessGauge({ value, className = "" }: { value: number; className?: string }) {
  const [displayValue, setDisplayValue] = useState(0);
  const elementRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      if (entries[0]?.isIntersecting) {
        let start = 0; const end = value; const increment = end / (1000 / 16);
        const timer = setInterval(() => {
          start += increment;
          if (start >= end) { clearInterval(timer); setDisplayValue(end); }
          else setDisplayValue(Math.floor(start));
        }, 16);
        observer.disconnect();
      }
    }, { threshold: 0.5 });
    if (elementRef.current) observer.observe(elementRef.current);
    return () => observer.disconnect();
  }, [value]);
  const dashArray = 126;
  const strokeDashoffset = dashArray - (dashArray * value) / 100;
  return (
    <div ref={elementRef} className={`flex flex-col items-center gap-2 ${className}`}>
      <div className="relative w-[100px] h-[50px] overflow-hidden">
        <svg viewBox="0 0 100 50" className="w-full h-full overflow-visible">
          <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="var(--line)" strokeWidth="8" strokeLinecap="round" />
          <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="var(--gold)" strokeWidth="8" strokeLinecap="round"
            style={{ strokeDasharray: dashArray, strokeDashoffset, transition: "stroke-dashoffset 1s ease-out" }} />
        </svg>
        <div className="absolute bottom-0 left-0 w-full text-center font-mono text-2xl font-medium tnum">{displayValue}</div>
      </div>
      <div className="text-[13px] text-muted-foreground font-mono uppercase tracking-wider">reviewed findings only</div>
    </div>
  );
}

export function DealBreakerPill({ state }: { state: "GO" | "REVIEW" | "STOP" }) {
  const styles = {
    GO: "border-muted-foreground text-muted-foreground",
    REVIEW: "border-[#D4812A] text-[#D4812A]",
    STOP: "border-destructive text-destructive",
  };
  return <div className={`px-3 py-1 rounded-[6px] border text-[13px] font-mono tracking-wider font-medium ${styles[state]}`}>{state}</div>;
}

export function Button({ children, variant = "primary", className = "", ...props }:
  React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" }) {
  const base = "inline-flex items-center justify-center px-5 py-2.5 rounded-[6px] font-medium transition-all focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background disabled:opacity-50 disabled:cursor-not-allowed";
  const variants = {
    primary: "bg-primary text-primary-foreground hover:brightness-110",
    ghost: "bg-transparent text-foreground border border-border hover:bg-border",
  };
  return <button className={`${base} ${variants[variant]} ${className}`} {...props}>{children}</button>;
}

export function FadeIn({ children, className = "", delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);
  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry?.isIntersecting) { setIsVisible(true); observer.disconnect(); }
    }, { threshold: 0.1 });
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);
  return (
    <div ref={ref} className={`${className} ${isVisible ? "fade-in-slide" : "opacity-0"}`} style={{ animationDelay: `${delay}ms` }}>
      {children}
    </div>
  );
}

export function AnimatedNumber({ value, prefix = "", suffix = "" }: { value: number; prefix?: string; suffix?: string }) {
  const [displayValue, setDisplayValue] = useState(0);
  const elementRef = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      if (entries[0]?.isIntersecting) {
        let start = 0; const end = value; const increment = end / (2000 / 16);
        const timer = setInterval(() => {
          start += increment;
          if (start >= end) { clearInterval(timer); setDisplayValue(end); }
          else setDisplayValue(start);
        }, 16);
        observer.disconnect();
      }
    }, { threshold: 0.5 });
    if (elementRef.current) observer.observe(elementRef.current);
    return () => observer.disconnect();
  }, [value]);
  return <span ref={elementRef} className="tnum">{prefix}{Math.floor(displayValue).toLocaleString("en-US")}{suffix}</span>;
}

export function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || "";
  const router = useRouter();
  async function doLogout() { await logout(); router.push("/login"); router.refresh(); }
  const navLinks = [
    { href: "/contracts", label: "العقود" },
    { href: "/idea-check", label: "فحص الفكرة" },
    { href: "/register", label: "الالتزامات" },
    { href: "/monitoring", label: "الرصد" },
    { href: "/evidence", label: "الأدلة" },
    { href: "/admin", label: "الإدارة" },
  ];
  return (
    <div className="min-h-[100dvh] flex flex-col bg-background text-foreground">
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
        <div className="max-w-[1200px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/contracts" className="flex flex-col">
              <span className="font-bold text-xl leading-none">سند</span>
              <span className="font-mono text-[10px] text-muted-foreground leading-none mt-1">SANAD</span>
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              {navLinks.map((link) => (
                <Link key={link.href} href={link.href}
                  className={`text-[15px] transition-colors hover:text-primary ${pathname.startsWith(link.href) ? "text-primary font-medium" : "text-muted-foreground"}`}>
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <button onClick={doLogout} className="text-[13px] text-muted-foreground hover:text-foreground transition-colors">خروج</button>
          </div>
        </div>
      </header>
      <main className="flex-1 w-full max-w-[1200px] mx-auto px-6 py-8">{children}</main>
    </div>
  );
}
