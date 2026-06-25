import type { GrammarRule, RuleCategoryOption } from "./types";

export const rulesContract = {
  rules: "/api/v1/rules",
  categories: "/api/v1/rules/categories",
} as const;

export type RulesContract = {
  GrammarRule: GrammarRule;
  RuleCategoryOption: RuleCategoryOption;
};
