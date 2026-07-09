import { Page, expect } from "@playwright/test";

export const SEED_EMAIL = process.env.SEED_REVIEWER_EMAIL ?? "reviewer@sanad.local";
export const SEED_PASSWORD = process.env.SEED_DEFAULT_PASSWORD ?? "sanad-dev-password";

// Logs in through the UI. Returns true on success; callers skip when the backend/seed is
// unavailable so these E2E specs degrade gracefully off a full stack.
export async function login(page: Page): Promise<boolean> {
  await page.goto("/login");
  await page.getByLabel(/email|البريد/i).fill(SEED_EMAIL);
  await page.getByLabel(/password|كلمة/i).fill(SEED_PASSWORD);
  await page.getByRole("button", { name: /sign in|دخول/i }).click();
  try {
    await page.waitForURL("**/contracts", { timeout: 8000 });
    return true;
  } catch {
    return false;
  }
}

export async function expectRtl(page: Page): Promise<void> {
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
}
