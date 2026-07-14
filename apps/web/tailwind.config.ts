import type { Config } from "tailwindcss";

// Design tokens are the single source of truth (docs/style-guide.md). Colors reference
// CSS variables defined in app/globals.css so light/dark switch without duplicating values.
const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // shadcn-style semantic tokens (the sanadscreen design's classes) → CSS vars.
        background: "var(--bg)",
        foreground: "var(--ink)",
        border: "var(--line)",
        input: "var(--line)",
        ring: "var(--gold)",
        card: { DEFAULT: "var(--card-bg)", foreground: "var(--ink)" },
        popover: { DEFAULT: "var(--card-bg)", foreground: "var(--ink)" },
        primary: { DEFAULT: "var(--gold)", foreground: "#FFFFFF" },
        secondary: { DEFAULT: "var(--muted-bg)", foreground: "var(--ink)" },
        muted: { DEFAULT: "var(--muted-bg)", foreground: "var(--muted-text)" },
        accent: { DEFAULT: "var(--orange-bg)", foreground: "var(--gold)" },
        destructive: { DEFAULT: "var(--sev-red)", foreground: "#FFFFFF" },
        sharia: "var(--sharia)",
        // Back-compat keys for not-yet-ported pages.
        ink: "var(--ink)", paper: "var(--bg)", surface: "var(--card-bg)", line: "var(--line)",
        orange: { DEFAULT: "var(--gold)", ink: "var(--gold-ink)", bg: "var(--orange-bg)" },
        severity: {
          critical: "var(--sev-red)", high: "var(--sev-amber)", medium: "#8a6d1f",
          low: "#5a6b4f", ok: "var(--sharia)",
        },
      },
      fontFamily: {
        sans: ["var(--font-plex-arabic)", "system-ui", "sans-serif"],
        mono: ["var(--font-plex-mono)", "ui-monospace", "monospace"],
      },
      fontSize: {
        display: ["2.25rem", { lineHeight: "1.2", letterSpacing: "-0.01em", fontWeight: "600" }],
        h1: ["1.75rem", { lineHeight: "1.3", fontWeight: "600" }],
        h2: ["1.375rem", { lineHeight: "1.3", fontWeight: "600" }],
        h3: ["1.125rem", { lineHeight: "1.4", fontWeight: "500" }],
        body: ["1rem", { lineHeight: "1.7", fontWeight: "400" }],
        label: ["0.875rem", { lineHeight: "1.4", fontWeight: "500" }],
        caption: ["0.75rem", { lineHeight: "1.4", fontWeight: "300" }],
      },
      spacing: {
        // On-scale only: 4 8 12 16 24 32 48 64
        "1": "4px", "2": "8px", "3": "12px", "4": "16px",
        "6": "24px", "8": "32px", "12": "48px", "16": "64px",
      },
      borderRadius: {
        card: "8px", chip: "6px",
        lg: "var(--radius)", md: "8px", sm: "6px", xl: "12px",
      },
      maxWidth: { reading: "820px" },
    },
  },
  plugins: [],
};

export default config;
