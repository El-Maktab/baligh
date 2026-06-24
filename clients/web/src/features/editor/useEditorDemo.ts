import { useReducer } from "react";

import { BLANK_DRAFT_BODY, SEEDED_DRAFTS } from "./mockData";
import type {
  CorrectionCategory,
  CorrectionStatus,
  EditorDraft,
  EditorFormatting,
  EditorLineFormat,
  EditorListStyle,
  EditorTextRange,
  MockCorrection,
} from "./types";

export type EditorPanel = "navigation" | "corrections";
export type FilterValue = CorrectionCategory;

export type EditorDemoState = {
  drafts: EditorDraft[];
  activeDraftId: string;
  activeFilter: FilterValue;
  expandedCorrectionId: string | null;
  focusedCorrectionId: string | null;
  navigationOpen: boolean;
  correctionsOpen: boolean;
  nextDraftNumber: number;
};

type Action =
  | { type: "selectDraft"; draftId: string }
  | { type: "addDraft" }
  | { type: "updateTitle"; title: string }
  | { type: "updateBody"; body: string }
  | { type: "setFilter"; filter: FilterValue }
  | { type: "toggleExpanded"; correctionId: string }
  | { type: "focusCorrection"; correctionId: string | null }
  | { type: "acceptCorrection"; correctionId: string }
  | { type: "ignoreCorrection"; correctionId: string }
  | { type: "togglePanel"; panel: EditorPanel }
  | { type: "closePanel"; panel: EditorPanel }
  | { type: "toggleStrong"; range: EditorTextRange }
  | { type: "toggleEmphasis"; range: EditorTextRange }
  | { type: "cycleList"; range: EditorTextRange }
  | {
      type: "setAlign";
      range: EditorTextRange;
      align: EditorLineFormat["align"];
    };

const DEFAULT_LINE_FORMAT: EditorLineFormat = {
  list: "none",
  align: "start",
};

export function createInitialEditorState(): EditorDemoState {
  return {
    drafts: SEEDED_DRAFTS,
    activeDraftId: SEEDED_DRAFTS[0]?.id ?? "",
    activeFilter: "spelling",
    expandedCorrectionId: SEEDED_DRAFTS[0]?.corrections[0]?.id ?? null,
    focusedCorrectionId: SEEDED_DRAFTS[0]?.corrections[0]?.id ?? null,
    navigationOpen: false,
    correctionsOpen: false,
    nextDraftNumber: SEEDED_DRAFTS.length + 1,
  };
}

function updateDraft(
  drafts: EditorDraft[],
  draftId: string,
  updater: (draft: EditorDraft) => EditorDraft,
) {
  return drafts.map((draft) => (draft.id === draftId ? updater(draft) : draft));
}

function findEditBounds(previousBody: string, nextBody: string) {
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

function resolveCorrections(
  previousBody: string,
  nextBody: string,
  corrections: MockCorrection[],
) {
  const edit = findEditBounds(previousBody, nextBody);
  const delta = edit.nextEnd - edit.previousEnd;

  return corrections.map<MockCorrection>((correction) => {
    if (correction.status !== "active") return correction;

    const [start, end] = correction.span;
    let nextSpan: EditorTextRange = correction.span;

    if (start >= edit.previousEnd) {
      nextSpan = [start + delta, end + delta];
    } else if (end > edit.previousStart) {
      return {
        ...correction,
        status: "stale" satisfies CorrectionStatus,
      };
    }

    if (nextBody.slice(...nextSpan) !== correction.original) {
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

function toggleRange(ranges: EditorTextRange[], range: EditorTextRange) {
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

function reconcileFormatting(
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

function cycleListStyle(current: EditorListStyle): EditorListStyle {
  if (current === "none") return "bullet";
  if (current === "bullet") return "numbered";
  return "none";
}

export function getActiveDraft(state: EditorDemoState): EditorDraft {
  const draft =
    state.drafts.find((entry) => entry.id === state.activeDraftId) ??
    state.drafts[0];

  if (!draft) throw new Error("Editor demo requires at least one draft");
  return draft;
}

export function getVisibleCorrections(
  state: EditorDemoState,
  draft: EditorDraft,
) {
  return draft.corrections.filter((correction) => {
    if (correction.status === "accepted" || correction.status === "ignored") {
      return false;
    }
    return correction.category === state.activeFilter;
  });
}

export function getCorrectionCounts(draft: EditorDraft) {
  return draft.corrections.reduce(
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

function updateLineFormats(
  draft: EditorDraft,
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

export function editorDemoReducer(
  state: EditorDemoState,
  action: Action,
): EditorDemoState {
  const activeDraft = getActiveDraft(state);

  switch (action.type) {
    case "selectDraft":
      return {
        ...state,
        activeDraftId: action.draftId,
        expandedCorrectionId: null,
        focusedCorrectionId: null,
        navigationOpen: false,
      };
    case "addDraft": {
      const newDraft: EditorDraft = {
        id: `draft-${state.nextDraftNumber}`,
        title: `نص جديد ${state.nextDraftNumber}`,
        body: BLANK_DRAFT_BODY,
        stageLabel: "محلي فقط",
        updatedAt: "الآن",
        formatting: { strong: [], emphasis: [], lines: {} },
        corrections: [],
      };
      return {
        ...state,
        drafts: [newDraft, ...state.drafts],
        activeDraftId: newDraft.id,
        expandedCorrectionId: null,
        focusedCorrectionId: null,
        navigationOpen: false,
        nextDraftNumber: state.nextDraftNumber + 1,
      };
    }
    case "updateTitle":
      return {
        ...state,
        drafts: updateDraft(state.drafts, activeDraft.id, (draft) => ({
          ...draft,
          title: action.title,
          updatedAt: "الآن",
        })),
      };
    case "updateBody":
      return {
        ...state,
        drafts: updateDraft(state.drafts, activeDraft.id, (draft) => ({
          ...draft,
          body: action.body,
          updatedAt: "الآن",
          formatting: reconcileFormatting(
            draft.formatting,
            draft.body,
            action.body,
          ),
          corrections: resolveCorrections(
            draft.body,
            action.body,
            draft.corrections,
          ),
        })),
      };
    case "setFilter":
      return {
        ...state,
        activeFilter: action.filter,
        expandedCorrectionId: null,
        focusedCorrectionId: null,
      };
    case "toggleExpanded":
      return {
        ...state,
        expandedCorrectionId:
          state.expandedCorrectionId === action.correctionId
            ? null
            : action.correctionId,
        focusedCorrectionId: action.correctionId,
      };
    case "focusCorrection":
      return { ...state, focusedCorrectionId: action.correctionId };
    case "acceptCorrection":
      return {
        ...state,
        drafts: updateDraft(state.drafts, activeDraft.id, (draft) => {
          const target = draft.corrections.find(
            (correction) => correction.id === action.correctionId,
          );
          if (!target || target.status === "stale") return draft;

          const [start, end] = target.span;
          if (draft.body.slice(start, end) !== target.original) {
            return {
              ...draft,
              corrections: draft.corrections.map((correction) =>
                correction.id === target.id
                  ? { ...correction, status: "stale" }
                  : correction,
              ),
            };
          }

          const nextBody =
            draft.body.slice(0, start) +
            target.replacement +
            draft.body.slice(end);
          const delta = target.replacement.length - (end - start);

          return {
            ...draft,
            body: nextBody,
            updatedAt: "الآن",
            formatting: reconcileFormatting(
              draft.formatting,
              draft.body,
              nextBody,
            ),
            corrections: draft.corrections.map((correction) => {
              if (correction.id === action.correctionId) {
                return { ...correction, status: "accepted" };
              }
              if (correction.status === "active" && correction.span[0] >= end) {
                return {
                  ...correction,
                  span: [
                    correction.span[0] + delta,
                    correction.span[1] + delta,
                  ],
                };
              }
              return correction;
            }),
          };
        }),
        expandedCorrectionId: null,
        focusedCorrectionId: null,
      };
    case "ignoreCorrection":
      return {
        ...state,
        drafts: updateDraft(state.drafts, activeDraft.id, (draft) => ({
          ...draft,
          updatedAt: "الآن",
          corrections: draft.corrections.map((correction) =>
            correction.id === action.correctionId
              ? { ...correction, status: "ignored" }
              : correction,
          ),
        })),
        expandedCorrectionId: null,
        focusedCorrectionId: null,
      };
    case "togglePanel":
      return action.panel === "navigation"
        ? { ...state, navigationOpen: !state.navigationOpen }
        : { ...state, correctionsOpen: !state.correctionsOpen };
    case "closePanel":
      return action.panel === "navigation"
        ? { ...state, navigationOpen: false }
        : { ...state, correctionsOpen: false };
    case "toggleStrong":
    case "toggleEmphasis": {
      const key = action.type === "toggleStrong" ? "strong" : "emphasis";
      return {
        ...state,
        drafts: updateDraft(state.drafts, activeDraft.id, (draft) => {
          const range = resolveFormattingRange(draft.body, action.range);
          return {
            ...draft,
            formatting: {
              ...draft.formatting,
              [key]: toggleRange(draft.formatting[key], range),
            },
          };
        }),
      };
    }
    case "cycleList":
      return {
        ...state,
        drafts: updateDraft(state.drafts, activeDraft.id, (draft) => {
          const firstLine =
            getSelectedLineIndices(draft.body, action.range)[0] ?? 0;
          const nextList = cycleListStyle(
            getLineFormat(draft.formatting, firstLine).list,
          );
          return {
            ...draft,
            formatting: {
              ...draft.formatting,
              lines: updateLineFormats(draft, action.range, (format) => ({
                ...format,
                list: nextList,
              })),
            },
          };
        }),
      };
    case "setAlign":
      return {
        ...state,
        drafts: updateDraft(state.drafts, activeDraft.id, (draft) => ({
          ...draft,
          formatting: {
            ...draft.formatting,
            lines: updateLineFormats(draft, action.range, (format) => ({
              ...format,
              align: action.align,
            })),
          },
        })),
      };
    default:
      return state;
  }
}

export function useEditorDemo() {
  const [state, dispatch] = useReducer(
    editorDemoReducer,
    undefined,
    createInitialEditorState,
  );
  const activeDraft = getActiveDraft(state);
  const correctionCounts = getCorrectionCounts(activeDraft);
  const visibleCorrections = getVisibleCorrections(state, activeDraft);

  return {
    state,
    activeDraft,
    correctionCounts,
    visibleCorrections,
    selectDraft: (draftId: string) =>
      dispatch({ type: "selectDraft", draftId }),
    addDraft: () => dispatch({ type: "addDraft" }),
    updateTitle: (title: string) => dispatch({ type: "updateTitle", title }),
    updateBody: (body: string) => dispatch({ type: "updateBody", body }),
    setFilter: (filter: FilterValue) => dispatch({ type: "setFilter", filter }),
    toggleExpanded: (correctionId: string) =>
      dispatch({ type: "toggleExpanded", correctionId }),
    focusCorrection: (correctionId: string | null) =>
      dispatch({ type: "focusCorrection", correctionId }),
    acceptCorrection: (correctionId: string) =>
      dispatch({ type: "acceptCorrection", correctionId }),
    ignoreCorrection: (correctionId: string) =>
      dispatch({ type: "ignoreCorrection", correctionId }),
    togglePanel: (panel: EditorPanel) =>
      dispatch({ type: "togglePanel", panel }),
    closePanel: (panel: EditorPanel) => dispatch({ type: "closePanel", panel }),
    toggleStrong: (range: EditorTextRange) =>
      dispatch({ type: "toggleStrong", range }),
    toggleEmphasis: (range: EditorTextRange) =>
      dispatch({ type: "toggleEmphasis", range }),
    cycleList: (range: EditorTextRange) =>
      dispatch({ type: "cycleList", range }),
    setAlign: (range: EditorTextRange, align: EditorLineFormat["align"]) =>
      dispatch({ type: "setAlign", range, align }),
  };
}
