import { describe, expect, it } from "vitest";
import { apiError } from "../test/utils";
import { errorMessage } from "./api";

describe("errorMessage", () => {
  it("lists field errors from validation responses", () => {
    const err = apiError(422, {
      code: "validation_error",
      message: "Some fields are invalid",
      details: [{ field: "amount", message: "Input should be greater than 0" }],
    });
    expect(errorMessage(err)).toBe("amount: Input should be greater than 0");
  });

  it("uses the API message, then a network message, then the fallback", () => {
    expect(errorMessage(apiError(409, { code: "conflict", message: "Already exists" }))).toBe(
      "Already exists",
    );
    expect(errorMessage({ request: {} })).toMatch(/can't reach the server/i);
    expect(errorMessage(new Error("boom"), "Fallback")).toBe("Fallback");
  });
});
