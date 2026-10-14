import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { InsightList } from "./InsightsCard";

describe("InsightList", () => {
  it("shows each insight's title and explanation", () => {
    render(
      <InsightList
        insights={[
          {
            kind: "spike",
            tone: "warning",
            title: "Dining is 60% above usual",
            detail: "$240 vs $150.",
          },
          { kind: "unknown_kind", tone: "info", title: "Something new", detail: "Still rendered." },
        ]}
      />,
    );
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(screen.getByText("Dining is 60% above usual")).toBeInTheDocument();
    expect(screen.getByText("Still rendered.")).toBeInTheDocument();
  });
});
