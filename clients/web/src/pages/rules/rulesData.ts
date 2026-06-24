import { normalizeArabic } from "../mo3gm/dictionaryData";

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

export const ruleCategories: Array<{
  value: "all" | RuleCategory;
  label: string;
}> = [
  { value: "all", label: "الكل" },
  { value: "syntax", label: "النحو" },
  { value: "orthography", label: "الإملاء" },
  { value: "semantics", label: "الاستعمال" },
];

export const grammarRules: GrammarRule[] = [
  {
    id: "SY_LAM_JUSSIVE",
    category: "syntax",
    subtype: "jussive_operator",
    tier: "tier_1_rule_derived",
    title: "جزم المضارع بعد «لم»",
    explanation:
      "تدخل «لم» على الفعل المضارع فتنفي حدوثه في الماضي وتجزمه. تظهر علامة الجزم بالسكون أو حذف حرف العلة أو حذف النون.",
    incorrect: "لم يكتبونَ الرسالة.",
    correct: "لم يكتبوا الرسالة.",
    note: "حُذفت النون لأن الفعل من الأفعال الخمسة.",
  },
  {
    id: "SY_INNA_SISTERS_DUAL_ACCUSATIVE",
    category: "syntax",
    subtype: "inna_sisters_case",
    tier: "tier_1_rule_derived",
    title: "اسم إنّ وأخواتها",
    explanation:
      "تنصب إنّ وأخواتها الاسم وترفع الخبر. إذا كان الاسم مثنّى ظهرت علامة النصب بالياء.",
    incorrect: "إنّ الطالبان مجتهدان.",
    correct: "إنّ الطالبين مجتهدان.",
    note: "«الطالبين» اسم إنّ منصوب بالياء لأنه مثنّى.",
  },
  {
    id: "OT_ALIF_MAQSURA_ALA",
    category: "orthography",
    subtype: "alif_maqsura",
    tier: "tier_1_rule_derived",
    title: "الألف المقصورة في «على»",
    explanation:
      "تُكتب الألف اللينة في آخر حرف الجر «على» بصورة الياء غير المنقوطة، ولا تُكتب ياءً منقوطة.",
    incorrect: "وضعتُ الكتاب علي الطاولة.",
    correct: "وضعتُ الكتاب على الطاولة.",
    note: "الصواب ثابت في رسم حرف الجر: «على».",
  },
  {
    id: "OT_TA_MARBUTA_NOUN",
    category: "orthography",
    subtype: "ta_marbuta",
    tier: "tier_1_rule_derived",
    title: "التاء المربوطة في الاسم المؤنث",
    explanation:
      "تنتهي أسماء مؤنثة كثيرة بتاء مربوطة. تُنطق هاءً عند الوقف وتاءً عند الوصل، لكنها تُكتب «ة» في الحالين.",
    incorrect: "هذه شجره جميلة.",
    correct: "هذه شجرة جميلة.",
    note: "لا يحكم النطق عند الوقف وحده على رسم الكلمة.",
  },
  {
    id: "OT_TANWIN_NASB_ON_ALIF",
    category: "orthography",
    subtype: "tanwin",
    tier: "tier_1_rule_derived",
    title: "موضع تنوين النصب",
    explanation:
      "يوضع تنوين النصب على الحرف السابق لألف الزيادة، لا على الألف نفسها.",
    incorrect: "قرأت كتاباً مفيداً.",
    correct: "قرأت كتابًا مفيدًا.",
    note: "تأتي الفتحتان فوق الحرف المنوّن: الباء والدال هنا.",
  },
  {
    id: "SE_DECADES_IYAT",
    category: "semantics",
    subtype: "lexical_usage",
    tier: "tier_1_rule_derived",
    title: "صياغة أسماء العقود",
    explanation:
      "عند تسمية عقد زمني، تكون صيغة «ـينيات» أدق من الصيغة الشائعة المختصرة «ـينات».",
    incorrect: "ازدهر الفن في الثلاثينات.",
    correct: "ازدهر الفن في الثلاثينيات.",
    note: "هذه توصية في الاستعمال المعجمي وليست حكمًا إعرابيًا.",
  },
  {
    id: "SE_MOAKHARAN",
    category: "semantics",
    subtype: "lexical_usage",
    tier: "tier_1_rule_derived",
    title: "بدائل «مؤخرًا» الزمنية",
    explanation:
      "في السياق الزمني يمكن اختيار «حديثًا» أو «قريبًا» لتكون الدلالة أوضح وأفصح.",
    incorrect: "صدر الكتاب مؤخرًا.",
    correct: "صدر الكتاب حديثًا.",
    note: "البديل المقترح يتغيّر بحسب المعنى المقصود في الجملة.",
  },
];

const searchableRuleText = (rule: GrammarRule) =>
  normalizeArabic(
    [
      rule.id,
      rule.category,
      rule.subtype,
      rule.title,
      rule.explanation,
      rule.incorrect,
      rule.correct,
      rule.note,
    ].join(" "),
  ).toLocaleLowerCase("ar");

export function filterGrammarRules(
  rules: GrammarRule[],
  query: string,
  category: "all" | RuleCategory,
) {
  const normalizedQuery = normalizeArabic(query).toLocaleLowerCase("ar");
  return rules.filter(
    (rule) =>
      (category === "all" || rule.category === category) &&
      (!normalizedQuery || searchableRuleText(rule).includes(normalizedQuery)),
  );
}
