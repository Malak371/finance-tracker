import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import api from "../api/api";
import { apiError } from "../test/utils";
import ExpenseForm from "./ExpenseForm";

vi.mock("../api/api", async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, default: { ...actual.default, post: vi.fn(), put: vi.fn() } };
});

describe("ExpenseForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("creates an expense and reports it back", async () => {
    const saved = { id: 7, amount: 12.5, category: "Food", date: "2026-03-02", description: null };
    vi.mocked(api.post).mockResolvedValue({ data: saved });
    const onSaved = vi.fn();
    render(<ExpenseForm categories={["Food"]} onSaved={onSaved} onCancel={() => {}} />);

    await userEvent.type(screen.getByLabelText("Amount"), "12.50");
    await userEvent.clear(screen.getByLabelText("Date"));
    await userEvent.type(screen.getByLabelText("Date"), "2026-03-02");
    await userEvent.type(screen.getByLabelText("Category"), "Food");
    await userEvent.click(screen.getByRole("button", { name: "Add expense" }));

    expect(api.post).toHaveBeenCalledWith("/expenses", {
      amount: "12.5",
      category: "Food",
      date: "2026-03-02",
      description: null,
    });
    expect(onSaved).toHaveBeenCalledWith(saved);
  });

  it("edits an existing expense with PUT", async () => {
    const expense = {
      id: 3,
      amount: 9,
      category: "Fun",
      date: "2026-01-05",
      description: "Cinema",
    };
    vi.mocked(api.put).mockResolvedValue({ data: expense });
    render(<ExpenseForm expense={expense} onSaved={() => {}} onCancel={() => {}} />);

    expect(screen.getByLabelText("Amount")).toHaveValue(9);
    await userEvent.click(screen.getByRole("button", { name: "Save changes" }));

    expect(api.put).toHaveBeenCalledWith(
      "/expenses/3",
      expect.objectContaining({ description: "Cinema" }),
    );
  });

  it("shows field errors from the API and stays open", async () => {
    vi.mocked(api.post).mockRejectedValue(
      apiError(422, {
        code: "validation_error",
        message: "Some fields are invalid",
        details: [{ field: "date", message: "must be between 2000-01-01 and one year from today" }],
      }),
    );
    const onSaved = vi.fn();
    render(<ExpenseForm onSaved={onSaved} onCancel={() => {}} />);

    await userEvent.type(screen.getByLabelText("Amount"), "5");
    await userEvent.type(screen.getByLabelText("Category"), "Food");
    await userEvent.click(screen.getByRole("button", { name: "Add expense" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("date: must be between 2000-01-01");
    expect(onSaved).not.toHaveBeenCalled();
  });
});
