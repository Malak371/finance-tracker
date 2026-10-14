import { expect, test } from "@playwright/test";

test("sign up, track an expense against a budget, log out and back in", async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`;
  const password = "e2e-password-123";

  await page.goto("/signup");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign up" }).click();
  await expect(page).toHaveURL(/\/app$/);
  await expect(page.getByText(/No spending recorded/)).toBeVisible();

  await page.getByRole("link", { name: "Budgets" }).click();
  await page.getByRole("button", { name: "Add budget" }).click();
  const budgetForm = page.getByRole("form", { name: "Add budget" });
  await budgetForm.getByLabel("Category", { exact: true }).fill("Groceries");
  await budgetForm.getByLabel("Monthly limit").fill("100");
  await budgetForm.getByRole("button", { name: "Add budget" }).click();
  await expect(page.getByText("On track")).toBeVisible();

  await page.getByRole("link", { name: "Expenses" }).click();
  await page.getByRole("button", { name: "Add expense" }).first().click();
  const expenseForm = page.getByRole("form", { name: "Add expense" });
  await expenseForm.getByLabel("Amount").fill("85");
  await expenseForm.getByLabel("Category", { exact: true }).fill("groceries");
  await expenseForm.getByLabel("Description (optional)").fill("Weekly shop");
  await expenseForm.getByRole("button", { name: "Add expense" }).click();
  await expect(page.getByText("Weekly shop")).toBeVisible();

  await page.getByRole("link", { name: "Budgets" }).click();
  await expect(page.getByText("Nearing limit")).toBeVisible();

  await page.getByRole("button", { name: "Log out" }).last().click();
  await expect(page).toHaveURL(/\/$/);

  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill("wrong-password");
  await page.getByRole("button", { name: "Log in" }).click();
  await expect(page.getByRole("alert")).toContainText("Incorrect email or password");

  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Log in" }).click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
});

test("protected pages send signed-out visitors to log in", async ({ page }) => {
  await page.goto("/app/budgets");
  await expect(page).toHaveURL(/\/login$/);
});
