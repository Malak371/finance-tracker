import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderAt } from "../test/utils";
import { ProtectedRoute } from "./ProtectedRoute";

describe("ProtectedRoute", () => {
  it("sends signed-out visitors to the login page", () => {
    renderAt(
      <ProtectedRoute>
        <p>Secret dashboard</p>
      </ProtectedRoute>,
    );
    expect(screen.queryByText("Secret dashboard")).not.toBeInTheDocument();
    expect(screen.getByTestId("current-path")).toHaveTextContent("/login");
  });

  it("shows the page when signed in", () => {
    localStorage.setItem("token", "t");
    renderAt(
      <ProtectedRoute>
        <p>Secret dashboard</p>
      </ProtectedRoute>,
    );
    expect(screen.getByText("Secret dashboard")).toBeInTheDocument();
  });
});
