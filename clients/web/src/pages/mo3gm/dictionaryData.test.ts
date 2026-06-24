import { describe, expect, it } from "vitest";

import {
  findDictionaryEntry,
  normalizeArabic,
  updateRecentSearches,
} from "./dictionaryData";

describe("dictionary data", () => {
  it("normalizes whitespace, tatweel, and Arabic diacritics", () => {
    expect(normalizeArabic("  بَـلِيغٌ  ")).toBe("بليغ");
  });

  it("looks up a normalized Arabic word", () => {
    expect(findDictionaryEntry("بَـلِيغ")?.root).toBe("ب ل غ");
    expect(findDictionaryEntry("غير موجود")).toBeUndefined();
  });

  it("moves a search to the front without duplicates", () => {
    expect(updateRecentSearches(["بليغ", "جذر", "متوارث"], "جذر")).toEqual([
      "جذر",
      "بليغ",
      "متوارث",
    ]);
  });
});
