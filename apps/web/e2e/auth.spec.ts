import { test, expect } from "@playwright/test";
import { expectRtl } from "./helpers";

// These run against just the web server (no backend needed).
test.describe("login page", () => {
  test("renders Arabic-first and RTL", async ({ page }) => {
    await page.goto("/login");
    await expectRtl(page);
    await expect(page.locator("html")).toHaveAttribute("lang", "ar");
    await expect(page.getByText("سَنَد")).toBeVisible();
  });

  test("shows an error when credentials are rejected", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email|البريد/i).fill("nobody@sanad.local");
    await page.getByLabel(/password|كلمة/i).fill("wrong-password");
    await page.getByRole("button", { name: /sign in|دخول/i }).click();
    // Login failure keeps us on /login and surfaces the error copy.
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByText(/invalid credentials|بيانات الدخول غير صحيحة/i)).toBeVisible();
  });

  test("language toggle switches to English/LTR", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("button", { name: /EN|ع/ }).click();
    await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
  });
});
