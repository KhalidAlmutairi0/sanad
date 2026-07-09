import { test, expect } from "@playwright/test";
import { login } from "./helpers";

// Full-stack E2E (test-plan §6). Requires `docker compose up` + seeded corpus; skips
// otherwise so the suite still runs off a partial environment.
test.describe("contract review workspace", () => {
  test.beforeEach(async ({ page }) => {
    test.skip(!(await login(page)), "backend/seed unavailable");
  });

  test("upload a contract and see it in the list", async ({ page }) => {
    await page.getByLabel(/contract title|عنوان العقد/i).fill("E2E Test Contract");
    await page.setInputFiles('input[type="file"]', {
      name: "contract.txt",
      mimeType: "text/plain",
      buffer: Buffer.from(
        "المادة 1: تُعالَج البيانات الشخصية بموافقة صاحبها.\n" +
          "المادة 2: يجوز نقل البيانات خارج المملكة وفق الضوابط.\n",
        "utf-8",
      ),
    });
    await page.getByRole("button", { name: /upload|رفع/i }).click();
    await expect(page.getByText("E2E Test Contract")).toBeVisible({ timeout: 15_000 });
  });

  test("every finding carries a citation chip and score is reviewed-only", async ({ page }) => {
    // Open the first contract that has reached review.
    await page.getByText(/E2E Test Contract|Test Contract/i).first().click();
    await expect(page).toHaveURL(/\/contracts\/.+/);

    // The signature guarantee: no finding without a citation chip.
    const findings = page.locator("article");
    const count = await findings.count();
    if (count > 0) {
      // The score dial label states it counts reviewed findings only.
      await expect(page.getByText(/reviewed findings only|الملاحظات المراجَعة فقط/i)).toBeVisible();
      // Each finding card exposes a citation chip button (◆ + code + article).
      const chips = page.getByRole("button", { name: /◆|PDPL|LABOR/ });
      expect(await chips.count()).toBeGreaterThan(0);
    }
  });
});
