import { expect, test } from "@playwright/test";

test("a visitor can explore the demo from the landing page", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Know where your money goes");

  await page.getByRole("button", { name: "Explore the live demo" }).first().click();

  await expect(page).toHaveURL(/\/app$/);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByText(/You're exploring a demo account/)).toBeVisible();
  await expect(page.getByRole("alert").filter({ hasText: "Budget alert" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Insights" })).toBeVisible();

  await page.getByRole("link", { name: "Recurring" }).click();
  await expect(page.getByText("NETFLIX.COM")).toBeVisible();
  await expect(page.getByText(/Up from \$15\.49/)).toBeVisible();
});

test("importing the sample statement flags duplicates and suggests categories", async ({ page }) => {
  await page.goto("/demo");
  await expect(page).toHaveURL(/\/app$/);

  await page.getByRole("link", { name: "Import" }).click();
  await page.getByRole("button", { name: "Use a sample statement" }).click();
  await page.getByRole("button", { name: "Preview transactions" }).click();

  await expect(page.getByText(/already recorded \(unticked\)/)).toBeVisible();
  await expect(page.getByText("Your rule").first()).toBeVisible();
  await expect(page.getByText("Needs a category").first()).toBeVisible();

  const yoga = page.getByLabel("Category for ZEN FLOW YOGA STUDIO");
  await yoga.fill("Health");
  await expect(page.getByText("Edited")).toBeVisible();

  await page.getByRole("button", { name: /^Import \d+ expenses?/ }).click();
  await expect(page.getByRole("heading", { name: /^Imported \d+ expenses?$/ })).toBeVisible();

  await page.getByRole("link", { name: "View expenses" }).click();
  await expect(page.getByText("ZEN FLOW YOGA STUDIO")).toBeVisible();
});
