import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import api from "../api/api";
import { renderAt } from "../test/utils";
import DemoStart from "./DemoStart";

vi.mock("../api/api", async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, default: { ...actual.default, post: vi.fn() } };
});

describe("DemoStart", () => {
  it("creates a demo account once and opens the app", async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { access_token: "demo-token" } });
    renderAt(<DemoStart />, { path: "/demo" });

    await waitFor(() => expect(screen.getByTestId("current-path")).toHaveTextContent("/app"));
    expect(api.post).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem("token")).toBe("demo-token");
  });
});
