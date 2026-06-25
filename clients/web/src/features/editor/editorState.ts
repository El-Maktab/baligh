import type {
  Correction,
  CorrectionCounts,
  CorrectionStatus,
  DraftDocument,
  EditorFormatting,
  EditorLineFormat,
  EditorListStyle,
  EditorSelection,
  EditorTextRange,
  TashkeelResult,
} from "./types";

const DEFAULT_LINE_FORMAT: EditorLineFormat = {
  list: "none",
  align: "start",
};

const ARABIC_WORD_RE = /[\u0621-\u063a\u0641-\u064a]+/g;

const TASHKEEL_MAP: Record<string, string> = {
  المحبة: "المَحَبَّة",
  تتأنى: "تَتَأَنَّى",
  وترفق: "وَتَرفُق",
  ترفّق: "تَرَفَّق",
  لا: "لَا",
  تحسد: "تَحسُد",
  تتفاخر: "تَتَفَاخَر",
  تفتخر: "تَفتَخِر",
  ولا: "وَلَا",
  تنتفخ: "تَنتَفِخ",
  تقبح: "تَقبُح",
  تطلب: "تَطلُب",
  لنفسها: "لِنَفسِهَا",
  تحتد: "تَحتَد",
  تظن: "تَظُن",
  السوء: "السُّوءَ",
  تفرح: "تَفرَح",
  بالإثم: "بِالإِثم",
  بالحق: "بِالحَق",
  وتحتمل: "وَتَحتَمِل",
  كل: "كُلّ",
  شيء: "شَيء",
  وتصدق: "وَتُصَدِّق",
  وترجو: "وَتَرجُو",
  وتصبر: "وَتَصبِر",
  تسقط: "تَسقُط",
  أبداً: "أَبَدًا",
  يجب: "يَجِب",
  على: "عَلَى",
  الكاتب: "الكَاتِب",
  أن: "أَن",
  يعتن: "يَعتَنِ",
  يعتني: "يَعتَنِي",
  بالتفاصيل: "بِالتَّفَاصِيل",
  الدقيقة: "الدَّقِيقَة",
  وأن: "وَأَن",
  يختار: "يَختَار",
  تعبيرات: "تَعبِيرَات",
  مناسبة: "مُنَاسِبَة",
  جدا: "جِدًّا",
  للسياق: "لِلسِّيَاق",
  المقصود: "المَقصُود",
  أكتب: "أَكتُب",
  هذه: "هَذِهِ",
  الرسالة: "الرِّسَالَة",
  لأشارك: "لِأُشَارِكَ",
  الفريق: "الفَرِيق",
  ملاحظات: "مُلَاحَظَات",
  أولية: "أَوَّلِيَّة",
  حول: "حَول",
  الصفحة: "الصَّفحَة",
  الجديدة: "الجَدِيدَة",
  يفيدني: "يُفِيدُنِي",
  المحرر: "المُحَرِّر",
  في: "فِي",
  ترتيب: "تَرتِيب",
  الأفكار: "الأَفكَار",
  وضبط: "وَضَبط",
  علامات: "عَلَامَات",
  الترقيم: "التَّرقِيم",
  ومراجعة: "وَمُرَاجَعَة",
  بعض: "بَعض",
  الصياغات: "الصِّيَاغَات",
  قبل: "قَبل",
  الإرسال: "الإِرسَال",
  ابدأ: "ابدَأ",
  كتابة: "كِتَابَة",
  نص: "نَصّ",
  جديد: "جَدِيد",
  هنا: "هُنَا",
  سيبقى: "سَيَبقَى",
  هذا: "هَذَا",
  النموذج: "النَّمُوذَج",
  محلياً: "مَحَلِّيًّا",
  داخل: "دَاخِل",
  الواجهة: "الوَاجِهَة",
  إلى: "إِلَى",
  نربطه: "نَربِطُه",
  بالخلفية: "بِالخَلفِيَّة",
  لاحقاً: "لَاحِقًا",
};

export function selectionToRange(selection: EditorSelection): EditorTextRange {
  return [selection.start, selection.end];
}

export function rangeToSelection(range: EditorTextRange): EditorSelection {
  return { start: range[0], end: range[1] };
}

export function findEditBounds(previousBody: string, nextBody: string) {
  let prefix = 0;
  const sharedLength = Math.min(previousBody.length, nextBody.length);

  while (prefix < sharedLength && previousBody[prefix] === nextBody[prefix]) {
    prefix += 1;
  }

  let suffix = 0;
  while (
    suffix < previousBody.length - prefix &&
    suffix < nextBody.length - prefix &&
    previousBody[previousBody.length - suffix - 1] ===
      nextBody[nextBody.length - suffix - 1]
  ) {
    suffix += 1;
  }

  return {
    previousStart: prefix,
    previousEnd: previousBody.length - suffix,
    nextEnd: nextBody.length - suffix,
  };
}

export function resolveCorrections(
  previousBody: string,
  nextBody: string,
  corrections: Correction[],
) {
  const edit = findEditBounds(previousBody, nextBody);
  const delta = edit.nextEnd - edit.previousEnd;

  return corrections.map<Correction>((correction) => {
    if (correction.status !== "active") return correction;

    const { start, end } = correction.span;
    let nextSpan = correction.span;

    if (start >= edit.previousEnd) {
      nextSpan = { start: start + delta, end: end + delta };
    } else if (end > edit.previousStart) {
      return {
        ...correction,
        status: "stale" satisfies CorrectionStatus,
      };
    }

    if (nextBody.slice(nextSpan.start, nextSpan.end) !== correction.original) {
      return {
        ...correction,
        span: nextSpan,
        status: "stale" satisfies CorrectionStatus,
      };
    }

    return { ...correction, span: nextSpan };
  });
}

function normalizeRanges(ranges: EditorTextRange[]) {
  return [...ranges]
    .filter(([start, end]) => end > start)
    .sort((left, right) => left[0] - right[0])
    .reduce<EditorTextRange[]>((result, range) => {
      const previous = result.at(-1);
      if (previous && range[0] <= previous[1]) {
        previous[1] = Math.max(previous[1], range[1]);
      } else {
        result.push([...range]);
      }
      return result;
    }, []);
}

function subtractRange(
  ranges: EditorTextRange[],
  [removeStart, removeEnd]: EditorTextRange,
) {
  return ranges.flatMap<EditorTextRange>(([start, end]) => {
    if (end <= removeStart || start >= removeEnd) return [[start, end]];

    const remaining: EditorTextRange[] = [];
    if (start < removeStart) remaining.push([start, removeStart]);
    if (end > removeEnd) remaining.push([removeEnd, end]);
    return remaining;
  });
}

export function isRangeCovered(
  ranges: EditorTextRange[],
  [start, end]: EditorTextRange,
) {
  return end > start && ranges.some(([from, to]) => from <= start && to >= end);
}

export function toggleRange(ranges: EditorTextRange[], range: EditorTextRange) {
  return isRangeCovered(ranges, range)
    ? subtractRange(ranges, range)
    : normalizeRanges([...ranges, range]);
}

function reconcileRanges(
  ranges: EditorTextRange[],
  previousBody: string,
  nextBody: string,
) {
  const edit = findEditBounds(previousBody, nextBody);
  const delta = edit.nextEnd - edit.previousEnd;
  const insertion = edit.previousStart === edit.previousEnd;

  return normalizeRanges(
    ranges.flatMap<EditorTextRange>(([start, end]) => {
      if (end <= edit.previousStart) return [[start, end]];
      if (start >= edit.previousEnd) return [[start + delta, end + delta]];
      if (
        insertion &&
        start <= edit.previousStart &&
        end >= edit.previousStart
      ) {
        return [[start, end + delta]];
      }
      return [];
    }),
  );
}

function countLineBreaks(value: string) {
  return [...value].filter((character) => character === "\n").length;
}

function reconcileLineFormats(
  lines: EditorFormatting["lines"],
  previousBody: string,
  nextBody: string,
) {
  const edit = findEditBounds(previousBody, nextBody);
  const editLine = countLineBreaks(previousBody.slice(0, edit.previousStart));
  const removedLines = countLineBreaks(
    previousBody.slice(edit.previousStart, edit.previousEnd),
  );
  const insertedLines = countLineBreaks(
    nextBody.slice(edit.previousStart, edit.nextEnd),
  );
  const lineDelta = insertedLines - removedLines;

  return Object.fromEntries(
    Object.entries(lines).map(([line, format]) => {
      const lineIndex = Number(line);
      return [lineIndex > editLine ? lineIndex + lineDelta : lineIndex, format];
    }),
  );
}

export function reconcileFormatting(
  formatting: EditorFormatting,
  previousBody: string,
  nextBody: string,
): EditorFormatting {
  return {
    strong: reconcileRanges(formatting.strong, previousBody, nextBody),
    emphasis: reconcileRanges(formatting.emphasis, previousBody, nextBody),
    lines: reconcileLineFormats(formatting.lines, previousBody, nextBody),
  };
}

export function resolveFormattingRange(
  body: string,
  [anchor, focus]: EditorTextRange,
): EditorTextRange {
  const start = Math.max(0, Math.min(anchor, focus, body.length));
  const end = Math.max(0, Math.min(Math.max(anchor, focus), body.length));
  if (start !== end) return [start, end];

  const lineStart = body.lastIndexOf("\n", Math.max(0, start - 1)) + 1;
  const nextBreak = body.indexOf("\n", start);
  return [lineStart, nextBreak === -1 ? body.length : nextBreak];
}

export function getSelectedLineIndices(body: string, range: EditorTextRange) {
  const [start, end] = resolveFormattingRange(body, range);
  const firstLine = countLineBreaks(body.slice(0, start));
  const effectiveEnd = Math.max(start, end - 1);
  const lastLine = countLineBreaks(body.slice(0, effectiveEnd));
  return Array.from(
    { length: lastLine - firstLine + 1 },
    (_, index) => firstLine + index,
  );
}

export function getLineFormat(formatting: EditorFormatting, lineIndex: number) {
  return formatting.lines[lineIndex] ?? DEFAULT_LINE_FORMAT;
}

export function updateLineFormats(
  draft: DraftDocument,
  range: EditorTextRange,
  updater: (format: EditorLineFormat) => EditorLineFormat,
) {
  const selectedLines = getSelectedLineIndices(draft.body, range);
  return {
    ...draft.formatting.lines,
    ...Object.fromEntries(
      selectedLines.map((line) => [
        line,
        updater(getLineFormat(draft.formatting, line)),
      ]),
    ),
  };
}

export function cycleListStyle(current: EditorListStyle): EditorListStyle {
  if (current === "none") return "bullet";
  if (current === "bullet") return "numbered";
  return "none";
}

function applyTashkeelToText(text: string) {
  let applied = false;
  const nextText = text.replace(ARABIC_WORD_RE, (word) => {
    const replacement = TASHKEEL_MAP[word];
    if (!replacement || replacement === word) return word;
    applied = true;
    return replacement;
  });

  return { text: nextText, applied };
}

export function applyTashkeelToBody(
  body: string,
  range: EditorTextRange,
): TashkeelResult {
  const [start, end] = resolveFormattingRange(body, range);
  if (start >= end) return { body, applied: false };

  const { text, applied } = applyTashkeelToText(body.slice(start, end));
  if (!applied) return { body, applied: false };

  return {
    body: `${body.slice(0, start)}${text}${body.slice(end)}`,
    applied: true,
  };
}

export function getCorrectionCounts(
  corrections: Correction[],
): CorrectionCounts {
  return corrections.reduce(
    (counts, correction) => {
      if (correction.status === "accepted" || correction.status === "ignored") {
        return counts;
      }
      counts.all += 1;
      counts[correction.category] += 1;
      return counts;
    },
    { all: 0, spelling: 0, grammar: 0, style: 0 },
  );
}

export function replaceTextRange(
  body: string,
  range: EditorSelection,
  replacement: string,
) {
  return body.slice(0, range.start) + replacement + body.slice(range.end);
}

export function cloneDraftDocument(draft: DraftDocument): DraftDocument {
  return structuredClone(draft);
}
