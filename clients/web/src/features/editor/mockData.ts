import type { EditorDraft } from "./types";

export const DEFAULT_DRAFT_TITLE = "مسودة جديدة";

export const DEFAULT_DRAFT_BODY = "اكتب النص هنا...";

export const SEEDED_DRAFTS: EditorDraft[] = [
  {
    id: "draft-1",
    title: "عن المحبة",
    stageLabel: "قيد المراجعة",
    updatedAt: "منذ 4 دقائق",
    revision: 1,
    formatting: {
      strong: [],
      emphasis: [],
      lines: {},
    },
    body: [
      "المحبة تتأنى وترفق،",
      "المحبة لا تحسد. المحبة لا تتفاخر ولا تنتفخ،",
      "ولا تقبح، ولا تطلب ما لنفسها، ولا تحتد،",
      "ولا تظن السوء،",
      "لا تفرح بالإثم بل تفرح بالحق،",
      "",
      "وتحتمل كل شيء،",
      "وتصدق كل شيء،",
      "وترجو كل شيء،",
      "وتصبر على كل شيء،",
      "",
      "المحبة لا تسقط أبداً.",
      "يجب على الكاتب أن يعتن بالتفاصيل الدقيقة،",
      "وأن يختار تعبيرات مناسبة جدا جدا للسياق المقصود.",
    ].join("\n"),
    corrections: [
      {
        id: "correction-1",
        category: "spelling",
        status: "active",
        span: { start: 13, end: 18 },
        title: "ضبط الفعل",
        lineLabel: "سطر 1:4",
        original: "وترفق",
        replacement: "وترفّق",
        explanation:
          "النص المعروض في المرجع يبرز هذا الموضع بتصحيح ضبط بسيط داخل السطر.",
        ruleLabel: "قاعدة الضبط والسياق",
      },
      {
        id: "correction-2",
        category: "spelling",
        status: "active",
        span: { start: 43, end: 52 },
        title: "استبدال أدق",
        lineLabel: "السطر 2",
        original: "لا تتفاخر",
        replacement: "لا تفتخر",
        explanation:
          "هذا البديل أقرب للنبرة الهادئة في النص المرجعي ويقلل الثقل الإيقاعي.",
        ruleLabel: "بدائل الصياغة الشائعة",
      },
      {
        id: "correction-3",
        category: "grammar",
        status: "active",
        span: { start: 252, end: 256 },
        title: "فعل مضارع منصوب",
        lineLabel: "السطر 13",
        original: "يعتن",
        replacement: "يعتني",
        explanation: "الفعل هنا يحتاج إلى الياء ليبقى على صيغته الصحيحة.",
        ruleLabel: "أحكام الأفعال المعتلة",
      },
      {
        id: "correction-4",
        category: "style",
        status: "active",
        span: { start: 294, end: 308 },
        title: "صياغة أكثر دقة",
        lineLabel: "السطر 14",
        original: "مناسبة جدا جدا",
        replacement: "أدق وأكثر ملاءمة",
        explanation: "التكرار يضعف الإيقاع هنا، والصياغة البديلة أوضح.",
        ruleLabel: "تحسين الأسلوب وتخفيف التكرار",
      },
    ],
  },
  {
    id: "draft-2",
    title: "مسودة الرسالة",
    stageLabel: "مسودة سريعة",
    updatedAt: "منذ 12 دقيقة",
    revision: 1,
    formatting: {
      strong: [],
      emphasis: [],
      lines: {},
    },
    body: [
      "أكتب هذه الرسالة لأشارك الفريق ملاحظات أولية حول الصفحة الجديدة.",
      "يُفيدني المحرر في ترتيب الأفكار، وضبط علامات الترقيم، ومراجعة بعض الصياغات قبل الإرسال.",
    ].join("\n\n"),
    corrections: [],
  },
];

export const BLANK_DRAFT_BODY = [
  "ابدأ كتابة نص جديد هنا.",
  "سيبقى هذا النموذج محلياً داخل الواجهة إلى أن نربطه بالخلفية لاحقاً.",
].join("\n\n");
