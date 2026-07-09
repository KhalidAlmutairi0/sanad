import type { Metadata } from "next";
import { cookies } from "next/headers";
import { IBM_Plex_Sans_Arabic, IBM_Plex_Mono } from "next/font/google";
import { Providers, type Locale, type Theme } from "@/lib/i18n";
import "./globals.css";

// Self-hosted at build time (sovereignty: no runtime font CDN calls).
const plexArabic = IBM_Plex_Sans_Arabic({
  subsets: ["arabic", "latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-plex-arabic",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-plex-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "سَنَد SANAD",
  description: "منصة الامتثال السيادية — Zero Unsourced Findings",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const store = cookies();
  const locale = (store.get("sanad_locale")?.value as Locale) || "ar";
  const theme = (store.get("sanad_theme")?.value as Theme) || "light";
  const dir = locale === "ar" ? "rtl" : "ltr";

  return (
    <html
      lang={locale}
      dir={dir}
      className={`${plexArabic.variable} ${plexMono.variable} ${theme === "dark" ? "dark" : ""}`}
    >
      <body className="font-sans antialiased">
        <Providers initialLocale={locale} initialTheme={theme}>
          {children}
        </Providers>
      </body>
    </html>
  );
}
