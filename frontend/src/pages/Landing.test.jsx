import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { renderAt } from "../test/utils";
import Landing from "./Landing";

vi.mock("../api/api", async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, default: { ...actual.default, post: vi.fn(), get: vi.fn() } };
});

describe("Landing", () => {
  it("lets signed-out visitors explore without an account", () => {
    renderAt(<Landing />);
    expect(screen.getAllByRole("button", { name: /explore the live demo/i })).toHaveLength(2);
    expect(screen.getByRole("link", { name: "Create an account" })).toHaveAttribute(
      "href",
      "/signup",
    );
    // Feature previews render the real components with sample data.
    expect(screen.getByText("Over budget")).toBeInTheDocument();
    expect(screen.getByText("Your past choice")).toBeInTheDocument();
    expect(screen.getByText(/up from \$15\.49/i)).toBeInTheDocument();
  });

  it("sends signed-in visitors to their dashboard", () => {
    localStorage.setItem("token", "t");
    renderAt(<Landing />);
    expect(
      screen.queryByRole("button", { name: /explore the live demo/i }),
    ).not.toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /dashboard/i })[0]).toHaveAttribute("href", "/app");
  });
});
