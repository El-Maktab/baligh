import { describe, expect, it } from "vitest";

import {
  isShowcaseEnabled,
  resolveApiDataSource,
  resolveEditorDataSource,
  resolveMo3gmDataSource,
  resolveRulesDataSource,
} from "./environment";

describe("isShowcaseEnabled", () => {
  it("enables the showcase during local development", () => {
    expect(isShowcaseEnabled(true)).toBe(true);
  });

  it("enables the showcase for preview builds only when explicitly configured", () => {
    expect(isShowcaseEnabled(false, "true")).toBe(true);
    expect(isShowcaseEnabled(false, "false")).toBe(false);
    expect(isShowcaseEnabled(false)).toBe(false);
  });

  it("resolves the editor data source explicitly when configured", () => {
    expect(resolveEditorDataSource("mock", "http://localhost:8000")).toBe("mock");
    expect(resolveEditorDataSource("api", "http://localhost:8000")).toBe("api");
    expect(resolveEditorDataSource("auto", "http://localhost:8000")).toBe("auto");
  });

  it("shares the same resolution logic across the reference pages", () => {
    expect(resolveApiDataSource("mock", "http://localhost:8000")).toBe("mock");
    expect(resolveMo3gmDataSource("api", "http://localhost:8000")).toBe("api");
    expect(resolveRulesDataSource("auto", "http://localhost:8000")).toBe("auto");
  });

  it("defaults to auto when a backend URL exists and no mode is set", () => {
    expect(resolveEditorDataSource(undefined, "http://localhost:8000")).toBe("auto");
  });

  it("defaults to mock when no backend URL exists", () => {
    expect(resolveEditorDataSource()).toBe("mock");
  });
});
