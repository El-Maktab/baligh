export type DictionaryEntry = {
  word: string;
  vocalized: string;
  root: string;
  partOfSpeech: string;
  meanings: string[];
  synonyms: string[];
  antonyms: string[];
  examples: Array<{ source: string; text: string }>;
};

const ARABIC_DIACRITICS = /[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]/g;

export function normalizeArabic(value: string) {
  return value.trim().replaceAll("ـ", "").replace(ARABIC_DIACRITICS, "");
}

export const dictionaryEntries: DictionaryEntry[] = [
  {
    word: "بليغ",
    vocalized: "بَلِيغ",
    root: "ب ل غ",
    partOfSpeech: "صفة",
    meanings: [
      "حَسَنُ الكلام، فصيحُه، قويُّ تأثيره.",
      "بالغٌ غايته، شديدٌ ومؤثّر.",
    ],
    synonyms: ["فصيح", "مُفَوَّه", "مُبين", "طلق اللسان"],
    antonyms: ["عَيِيّ", "أبكم", "مُتلعثم"],
    examples: [
      {
        source: "سياق كلاسيكي",
        text: "قال الجاحظ: واللفظ البليغ من اللسان والمُحيي على الأيام.",
      },
      {
        source: "سياق حديث",
        text: "قدّم الكاتب وصفًا بليغًا لمعاناة اللاجئين في روايته الأخيرة.",
      },
    ],
  },
  {
    word: "استنبط",
    vocalized: "اِسْتَنْبَطَ",
    root: "ن ب ط",
    partOfSpeech: "فعل",
    meanings: [
      "استخرج معنى أو حكمًا بعد تأمّل وتفكير.",
      "استخرج الماء من منبعه.",
    ],
    synonyms: ["استخلص", "استنتج", "استخرج"],
    antonyms: ["أخفى", "أغفل"],
    examples: [
      { source: "سياق علمي", text: "استنبط الباحث النتيجة من شواهد متعددة." },
      { source: "سياق تعليمي", text: "استنبط الطالب القاعدة من الأمثلة." },
    ],
  },
  {
    word: "جذر",
    vocalized: "جِذْر",
    root: "ج ذ ر",
    partOfSpeech: "اسم",
    meanings: [
      "أصل النبات الممتد في الأرض.",
      "الأصل اللغوي الذي تُشتقّ منه الكلمات.",
    ],
    synonyms: ["أصل", "منشأ", "أساس"],
    antonyms: ["فرع", "غصن"],
    examples: [
      { source: "سياق لغوي", text: "تعود كلمة مكتبة إلى الجذر ك ت ب." },
      { source: "سياق طبيعي", text: "يمتد جذر الشجرة عميقًا في التربة." },
    ],
  },
  {
    word: "متوارث",
    vocalized: "مُتَوَارَث",
    root: "و ر ث",
    partOfSpeech: "صفة",
    meanings: ["منتقل من جيل إلى جيل.", "مأثور ومستمر عبر الزمن."],
    synonyms: ["موروث", "مأثور", "متناقل"],
    antonyms: ["مستحدث", "طارئ"],
    examples: [
      { source: "سياق ثقافي", text: "هذا تقليد متوارث في القرية منذ قرون." },
      {
        source: "سياق معرفي",
        text: "راجع الباحث رأيًا متوارثًا على ضوء الدليل.",
      },
    ],
  },
];

export function findDictionaryEntry(query: string) {
  const normalizedQuery = normalizeArabic(query);
  return dictionaryEntries.find(
    (entry) => normalizeArabic(entry.word) === normalizedQuery,
  );
}

export function updateRecentSearches(recent: string[], word: string) {
  return [word, ...recent.filter((item) => item !== word)].slice(0, 4);
}
