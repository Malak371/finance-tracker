import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import BudgetAlerts from "./BudgetAlerts";
import BudgetProgress from "./BudgetProgress";

const budget = (overrides) => ({
  id: 1,
  category: "Dining",
  amount: 200,
  spent: 100,
  remaining: 100,
  percent: 50,
  status: "ok",
  projected: null,
  ...overrides,
});

describe("BudgetProgress", () => {
  it("labels status with text, not only colour", () => {
    render(
      <BudgetProgress
        budget={budget({ spent: 230, remaining: -30, percent: 115, status: "over" })}
      />,
    );
    expect(screen.getByText("Over budget")).toBeInTheDocument();
    expect(screen.getByText(/\$30\.00 over/)).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "115");
  });

  it("warns when the current pace will exceed the limit", () => {
    render(<BudgetProgress budget={budget({ projected: 260 })} />);
    expect(screen.getByText(/on pace for \$260\.00/i)).toBeInTheDocument();
  });
});

describe("BudgetAlerts", () => {
  it("renders nothing when every budget is on track", () => {
    const { container } = render(<BudgetAlerts budgets={[budget()]} month="2026-03" />, {
      wrapper: MemoryRouter,
    });
    expect(container).toBeEmptyDOMElement();
  });

  it("summarises over and nearly-used budgets", () => {
    const budgets = [
      budget({ id: 1, status: "over", percent: 120 }),
      budget({ id: 2, category: "Shopping", status: "warning", percent: 85 }),
    ];
    render(<BudgetAlerts budgets={budgets} month="2026-03" />, { wrapper: MemoryRouter });
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Budget alert: 1 over the limit, 1 nearly used up",
    );
  });
});
