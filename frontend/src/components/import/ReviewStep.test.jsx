import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import api from "../../api/api";
import ReviewStep from "./ReviewStep";

vi.mock("../../api/api", async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, default: { ...actual.default, post: vi.fn() } };
});

const preview = {
  transactions: [
    {
      row: 1,
      date: "2026-03-01",
      amount: 4.5,
      description: "STARBUCKS",
      category: "Dining",
      category_source: "default",
      confidence: null,
      duplicate: false,
    },
    {
      row: 2,
      date: "2026-03-02",
      amount: 30,
      description: "ZEN YOGA",
      category: "Uncategorized",
      category_source: "none",
      confidence: null,
      duplicate: false,
    },
    {
      row: 3,
      date: "2026-03-03",
      amount: 9.99,
      description: "NETFLIX",
      category: "Subscriptions",
      category_source: "history",
      confidence: null,
      duplicate: true,
    },
  ],
  skipped: [{ row: 4, reason: "Money in (income or refund), not an expense" }],
};

describe("ReviewStep", () => {
  it("unticks duplicates and shows where each category came from", () => {
    render(<ReviewStep preview={preview} onImported={() => {}} onBack={() => {}} />);

    expect(screen.getByRole("checkbox", { name: "Import STARBUCKS" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Import NETFLIX" })).not.toBeChecked();
    expect(screen.getByText("Common merchant")).toBeInTheDocument();
    expect(screen.getByText("Needs a category")).toBeInTheDocument();
    expect(screen.getByText("1 rows skipped")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /import 2 expenses/i })).toBeEnabled();
  });

  it("sends corrected categories as manual so the categoriser learns from them", async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { imported: 2 } });
    const onImported = vi.fn();
    render(<ReviewStep preview={preview} onImported={onImported} onBack={() => {}} />);

    const yoga = screen.getByLabelText("Category for ZEN YOGA");
    await userEvent.clear(yoga);
    await userEvent.type(yoga, "Health");
    expect(screen.getByText("Edited")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /import 2 expenses/i }));

    const { transactions } = vi.mocked(api.post).mock.calls[0][1];
    expect(transactions.map((t) => [t.description, t.category, t.category_source])).toEqual([
      ["STARBUCKS", "Dining", "default"],
      ["ZEN YOGA", "Health", "manual"],
    ]);
    expect(onImported).toHaveBeenCalledWith(2);
  });
});
