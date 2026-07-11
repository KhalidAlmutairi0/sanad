import type { Metadata } from "next";
import { cookies } from "next/headers";
import localFont from "next/font/local";
import { IBM_Plex_Mono } from "next/font/google";
import { Providers, type Locale, type Theme } from "@/lib/i18n";
import "./globals.css";

// Thmanyah (خط ثمانية) — self-hosted (sovereignty: no runtime font CDN calls).
// One master maps to the whole weight range, so nothing is faux-bolded: typographic
// hierarchy comes from SIZE, not weight. Var name kept as --font-plex-arabic so the
// design tokens that reference it keep working.
const thmanyah = localFont({
  src: [{ path: "./fonts/thmanyah-sans-regular.otf", weight: "100 900", style: "normal" }],
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
      className={`${thmanyah.variable} ${plexMono.variable} ${theme === "dark" ? "dark" : ""}`}
    >
      <body className="font-sans antialiased">
        <Providers initialLocale={locale} initialTheme={theme}>
          {children}
        </Providers>
      </body>
    </html>
  );
}
