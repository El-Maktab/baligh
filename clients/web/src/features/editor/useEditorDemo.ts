import { useReducer } from "react";

import { BLANK_DRAFT_BODY, SEEDED_DRAFTS } from "./mockData";
import {
  applyTashkeelToBody,
  cycleListStyle,
  getCorrectionCounts,
  getLineFormat,
  getSelectedLineIndices,
  isRangeCovered,
  reconcileFormatting,
  resolveCorrections,
  resolveFormattingRange,
  toggleRange,
  updateLineFormats,
} from "./editorState";
import type {
  CorrectionCategory,
  DraftDocument,
  EditorLineFormat,
  EditorTextRange,
} from "./types";

export type EditorPanel = "navigation" | "corrections";
export type FilterValue = CorrectionCategory;

export type EditorDemoState = {
  drafts: DraftDocument[];
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
  | { type: "applyTashkeel"; range: EditorTextRange }
  | { type: "cycleList"; range: EditorTextRange }
  | {
      type: "setAlign";
      range: EditorTextRange;
      align: EditorLineFormat["align"];
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
  drafts: DraftDocument[],
  draftId: string,
  updater: (draft: DraftDocument) => DraftDocument,
) {
  return drafts.map((draft) => (draft.id === draftId ? updater(draft) : draft));
}

export function getActiveDraft(state: EditorDemoState): DraftDocument {
  const draft =
    state.drafts.find((entry) => entry.id === state.activeDraftId) ??
    state.drafts[0];

  if (!draft) throw new Error("Editor demo requires at least one draft");
  return draft;
}

export function getVisibleCorrections(
  state: EditorDemoState,
  draft: DraftDocument,
) {
  return draft.corrections.filter((correction) => {
    if (correction.status === "accepted" || correction.status === "ignored") {
      return false;
    }
    return correction.category === state.activeFilter;
  });
}

export function getDraftCorrectionCounts(draft: DraftDocument) {
  return getCorrectionCounts(draft.corrections);
}

export function applyTashkeel(body: string, range: EditorTextRange) {
  return applyTashkeelToBody(body, range);
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
      const newDraft: DraftDocument = {
        id: `draft-${state.nextDraftNumber}`,
        title: `نص جديد ${state.nextDraftNumber}`,
        body: BLANK_DRAFT_BODY,
        stageLabel: "محلي فقط",
        updatedAt: "الآن",
        revision: 1,
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
          if (
            !target ||
            target.status === "stale" ||
            target.kind !== "correction"
          ) {
            return draft;
          }

          const { start, end } = target.span;
          if (draft.body.slice(start, end) !== target.original) {
            return {
              ...draft,
              corrections: draft.corrections.map((correction) =>
                correction.id === target.id
                  ? { ...correction, status: "stale" as const }
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
                return { ...correction, status: "accepted" as const };
              }
              if (
                correction.status === "active" &&
                correction.span.start >= end
              ) {
                return {
                  ...correction,
                  span: {
                    start: correction.span.start + delta,
                    end: correction.span.end + delta,
                  },
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
              ? { ...correction, status: "ignored" as const }
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
    case "applyTashkeel":
      return {
        ...state,
        drafts: updateDraft(state.drafts, activeDraft.id, (draft) => {
          const result = applyTashkeelToBody(draft.body, action.range);
          if (!result.applied) return draft;

          return {
            ...draft,
            body: result.body,
            updatedAt: "الآن",
            formatting: reconcileFormatting(
              draft.formatting,
              draft.body,
              result.body,
            ),
            corrections: resolveCorrections(
              draft.body,
              result.body,
              draft.corrections,
            ),
          };
        }),
      };
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
  const correctionCounts = getDraftCorrectionCounts(activeDraft);
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
    applyTashkeel: (range: EditorTextRange) =>
      dispatch({ type: "applyTashkeel", range }),
    cycleList: (range: EditorTextRange) =>
      dispatch({ type: "cycleList", range }),
    setAlign: (range: EditorTextRange, align: EditorLineFormat["align"]) =>
      dispatch({ type: "setAlign", range, align }),
  };
}

export {
  getLineFormat,
  getSelectedLineIndices,
  isRangeCovered,
  resolveFormattingRange,
};

export { getDraftCorrectionCounts as getCorrectionCounts };
