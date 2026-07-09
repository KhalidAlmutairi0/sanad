import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { login } from "./helpers";

// Accessibility (test-plan §9): zero critical/serious axe violations.
test("login page has no critical accessibility violations", async ({ page }) => {
  await page.goto("/login");
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  const serious = results.violations.filter((v) => ["critical", "serious"].includes(v.impact ?? ""));
  expect(serious, JSON.stringify(serious, null, 2)).toEqual([]);
});

test("contracts page has no critical accessibility violations", async ({ page }) => {
  test.skip(!(await login(page)), "backend/seed unavailable");
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  const serious = results.violations.filter((v) => ["critical", "serious"].includes(v.impact ?? ""));
  expect(serious, JSON.stringify(serious, null, 2)).toEqual([]);
});
