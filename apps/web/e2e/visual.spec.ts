import { test, expect } from "@playwright/test";

// Visual regression (test-plan §7 UI-09). Baselines are generated on first run
// (`playwright test --update-snapshots`) and committed thereafter.
test("login page — light", async ({ page }) => {
  await page.goto("/login");
  await page.emulateMedia({ colorScheme: "light" });
  await expect(page).toHaveScreenshot("login-light.png", { maxDiffPixelRatio: 0.02 });
});

test("login page — dark", async ({ page }) => {
  await page.goto("/login");
  await page.emulateMedia({ colorScheme: "dark" });
  await expect(page).toHaveScreenshot("login-dark.png", { maxDiffPixelRatio: 0.02 });
});
