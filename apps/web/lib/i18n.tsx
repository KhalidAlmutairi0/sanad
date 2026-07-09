"use client";

import { createContext, useContext, useCallback, useEffect, useState } from "react";
import ar, { type Dict } from "@/locales/ar";
import en from "@/locales/en";

export type Locale = "ar" | "en";
export type Theme = "light" | "dark";

const DICTS: Record<Locale, Dict> = { ar, en };

interface Ctx {
  locale: Locale;
  dict: Dict;
  theme: Theme;
  toggleLocale: () => void;
  toggleTheme: () => void;
}

const AppContext = createContext<Ctx | null>(null);

function setCookie(name: string, value: string) {
  // Non-sensitive UI preferences only (never tokens). One year.
  document.cookie = `${name}=${value}; path=/; max-age=31536000; samesite=lax`;
}

export function Providers({
  children,
  initialLocale,
  initialTheme,
}: {
  children: React.ReactNode;
  initialLocale: Locale;
  initialTheme: Theme;
}) {
  const [locale, setLocale] = useState<Locale>(initialLocale);
  const [theme, setTheme] = useState<Theme>(initialTheme);

  useEffect(() => {
    const html = document.documentElement;
    html.lang = locale;
    html.dir = locale === "ar" ? "rtl" : "ltr";
  }, [locale]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  const toggleLocale = useCallback(() => {
    setLocale((l) => {
      const next = l === "ar" ? "en" : "ar";
      setCookie("sanad_locale", next);
      return next;
    });
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme((t) => {
      const next = t === "light" ? "dark" : "light";
      setCookie("sanad_theme", next);
      return next;
    });
  }, []);

  return (
    <AppContext.Provider value={{ locale, dict: DICTS[locale], theme, toggleLocale, toggleTheme }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp(): Ctx {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within Providers");
  return ctx;
}
