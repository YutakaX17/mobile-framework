import { describe, expect, it } from "vitest";

import { formatErrorMessage } from "./ErrorBoundary";

describe("error boundary", () => {
  it("formats error objects", () => {
    expect(formatErrorMessage(new Error("Route render failed"))).toBe("Route render failed");
  });

  it("formats string errors", () => {
    expect(formatErrorMessage("Unexpected route state")).toBe("Unexpected route state");
  });

  it("falls back for empty or unknown errors", () => {
    expect(formatErrorMessage(new Error(""))).toBe("An unexpected rendering error occurred.");
    expect(formatErrorMessage(undefined)).toBe("An unexpected rendering error occurred.");
  });
});
