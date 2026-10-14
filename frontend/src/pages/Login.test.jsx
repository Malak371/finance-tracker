import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import api from "../api/api";
import { apiError, renderAt } from "../test/utils";
import Login from "./Login";

vi.mock("../api/api", async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, default: { ...actual.default, post: vi.fn() } };
});

describe("Login", () => {
  beforeEach(() => {
    vi.mocked(api.post).mockReset();
  });

  it("logs in with the form-encoded credentials and goes to the dashboard", async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { access_token: "token-123" } });
    renderAt(<Login />, { path: "/login" });

    await userEvent.type(screen.getByLabelText("Email"), "me@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "secret-pass");
    await userEvent.click(screen.getByRole("button", { name: "Log in" }));

    const [url, body] = vi.mocked(api.post).mock.calls[0];
    expect(url).toBe("/auth/login");
    expect(body.toString()).toBe("username=me%40example.com&password=secret-pass");
    expect(localStorage.getItem("token")).toBe("token-123");
    expect(screen.getByTestId("current-path")).toHaveTextContent(/^\/$/);
  });

  it("shows the server's message when login fails", async () => {
    vi.mocked(api.post).mockRejectedValue(
      apiError(401, { code: "unauthorized", message: "Incorrect email or password" }),
    );
    renderAt(<Login />, { path: "/login" });

    await userEvent.type(screen.getByLabelText("Email"), "me@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "wrong");
    await userEvent.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Incorrect email or password");
    expect(localStorage.getItem("token")).toBeNull();
  });

  it("offers a one-click demo", async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { access_token: "demo-token" } });
    renderAt(<Login />, { path: "/login" });

    await userEvent.click(screen.getByRole("button", { name: /try the demo/i }));

    expect(api.post).toHaveBeenCalledWith("/auth/demo");
    expect(localStorage.getItem("token")).toBe("demo-token");
  });
});
