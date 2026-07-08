import type { Config } from "tailwindcss";

// Design tokens are the single source of truth (docs/style-guide.md). Colors reference
// CSS variables defined in app/globals.css so light/dark switch without duplicating values.
const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "var(--sanad-ink)",
        paper: "var(--sanad-paper)",
        surface: "var(--sanad-surface)",
        line: "var(--sanad-line)",
        muted: "var(--sanad-muted)",
        orange: {
          DEFAULT: "var(--sanad-orange)",
          ink: "var(--sanad-orange-ink)",
          bg: "var(--sanad-orange-bg)",
        },
        severity: {
          critical: "var(--sanad-critical)",
          high: "var(--sanad-high)",
          medium: "var(--sanad-medium)",
          low: "var(--sanad-low)",
          ok: "var(--sanad-ok)",
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
      borderRadius: { card: "8px", chip: "6px" },
      maxWidth: { reading: "820px" },
    },
  },
  plugins: [],
};

export default config;
