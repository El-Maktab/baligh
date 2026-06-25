export type RuleCategory = "syntax" | "orthography" | "semantics";

export type GrammarRule = {
  id: string;
  category: RuleCategory;
  subtype: string;
  tier: "tier_1_rule_derived";
  title: string;
  explanation: string;
  incorrect: string;
  correct: string;
  note: string;
};

export type RuleCategoryOption = {
  value: "all" | RuleCategory;
  label: string;
};
