import { describe, expect, it } from "vitest";

import { isShowcaseEnabled } from "./environment";

describe("isShowcaseEnabled", () => {
  it("enables the showcase during local development", () => {
    expect(isShowcaseEnabled(true)).toBe(true);
  });

  it("enables the showcase for preview builds only when explicitly configured", () => {
    expect(isShowcaseEnabled(false, "true")).toBe(true);
    expect(isShowcaseEnabled(false, "false")).toBe(false);
    expect(isShowcaseEnabled(false)).toBe(false);
  });
});
