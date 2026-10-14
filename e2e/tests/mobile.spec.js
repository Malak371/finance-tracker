import { expect, test } from "@playwright/test";

test("the app works on a phone without horizontal scrolling", async ({ page }) => {
  for (const path of ["/", "/login"]) {
    await page.goto(path);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, `${path} scrolls sideways`).toBeLessThanOrEqual(0);
  }

  await page.goto("/demo");
  await expect(page).toHaveURL(/\/app$/);
  for (const name of ["Dashboard", "Expenses", "Budgets", "Recurring", "Import", "Rules"]) {
    await expect(page.getByRole("link", { name, exact: true })).toBeVisible();
  }
  await page.getByRole("link", { name: "Budgets", exact: true }).click();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
});
