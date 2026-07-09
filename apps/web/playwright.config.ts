import { defineConfig, devices } from "@playwright/test";

// E2E runs against a running stack (docker compose up + seed). Override with BASE_URL.
const baseURL = process.env.BASE_URL ?? "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  // Keep local runs light (one worker, no parallel browsers). CI is where browsers should
  // fan out; bump workers there if needed.
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    locale: "ar",
  },
  // A single Chromium project. Dark theme is exercised via emulateMedia inside the specs,
  // so a separate dark project would just double the browser load for no extra coverage.
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
