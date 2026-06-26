import { describe, expect, it } from "vitest";

import { filterGrammarRules, grammarRules } from "./rulesData";

describe("rules filtering", () => {
  it("searches Arabic explanations, examples, and technical identifiers", () => {
    expect(
      filterGrammarRules(grammarRules, "الأفعال الخمسة", "all"),
    ).toHaveLength(1);
    expect(filterGrammarRules(grammarRules, "SY_INNA", "all")[0]?.id).toBe(
      "SY_INNA_SISTERS_DUAL_ACCUSATIVE",
    );
  });

  it("combines category and text filters", () => {
    expect(filterGrammarRules(grammarRules, "", "orthography")).toHaveLength(3);
    expect(filterGrammarRules(grammarRules, "", "punctuation")).toHaveLength(1);
    expect(
      filterGrammarRules(grammarRules, "مؤخرا", "orthography"),
    ).toHaveLength(0);
  });
});
