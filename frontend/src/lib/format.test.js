import { describe, expect, it } from "vitest";
import { monthRange, parseDate, shiftMonth } from "./format";

describe("month helpers", () => {
  it("shifts across year boundaries", () => {
    expect(shiftMonth("2026-01", -1)).toBe("2025-12");
    expect(shiftMonth("2025-12", 1)).toBe("2026-01");
  });

  it("knows the last day of each month, including leap years", () => {
    expect(monthRange("2028-02")).toEqual({ start: "2028-02-01", end: "2028-02-29" });
    expect(monthRange("2026-04").end).toBe("2026-04-30");
  });

  it("parses API dates as local dates, not UTC", () => {
    const d = parseDate("2026-03-01");
    expect([d.getFullYear(), d.getMonth(), d.getDate()]).toEqual([2026, 2, 1]);
  });
});
