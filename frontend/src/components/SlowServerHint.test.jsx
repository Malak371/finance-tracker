import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import SlowServerHint from "./SlowServerHint";

describe("SlowServerHint", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("explains a slow response after a few seconds, and hides once done", () => {
    const { rerender } = render(<SlowServerHint active />);
    expect(screen.queryByRole("status")).not.toBeInTheDocument();

    act(() => vi.advanceTimersByTime(4000));
    expect(screen.getByRole("status")).toHaveTextContent(/waking up the server/i);

    rerender(<SlowServerHint active={false} />);
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
