import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { EditorApiError, useEditorApi } from "./api";
import { DEFAULT_DRAFT_BODY, DEFAULT_DRAFT_TITLE } from "./mockData";
import {
  applyTashkeelToBody,
  cloneDraftDocument,
  cycleListStyle,
  getCorrectionCounts,
  getLineFormat,
  getSelectedLineIndices,
  isRangeCovered,
  rangeToSelection,
  reconcileFormatting,
  replaceTextRange,
  resolveCorrections,
  resolveFormattingRange,
  toggleRange,
  updateLineFormats,
} from "./editorState";
import { editorQueryKeys } from "./queryKeys";
import type {
  AnalysisState,
  Correction,
  CorrectionCategory,
  CorrectionCounts,
  DraftDocument,
  DraftSummary,
  EditorLineFormat,
  EditorSelection,
  EditorTextRange,
  SaveState,
  SuggestionItem,
  SuggestionMode,
} from "./types";

type EditorPanel = "navigation" | "corrections";
export type FilterValue = CorrectionCategory;

type SuggestionState = {
  status: "idle" | "loading" | "ready" | "error";
  isOpen: boolean;
  mode: SuggestionMode | null;
  highlightedIndex: number;
  replaceRange: EditorSelection | null;
  suggestions: SuggestionItem[];
  sessionId: string | null;
  errorMessage: string | null;
};

type AnchorRect = {
  top: number;
  left: number;
  width: number;
  height: number;
};

function defaultSuggestionState(): SuggestionState {
  return {
    status: "idle",
    isOpen: false,
    mode: null,
    highlightedIndex: 0,
    replaceRange: null,
    suggestions: [],
    sessionId: null,
    errorMessage: null,
  };
}

function isRevisionConflict(error: unknown): error is EditorApiError {
  return error instanceof EditorApiError && error.status === 409;
}

function extractLatestDraft(error: EditorApiError) {
  const payload = error.payload as { latestDraft?: DraftDocument } | undefined;
  return payload?.latestDraft;
}

function buildDraftSummary(draft: DraftDocument): DraftSummary {
  return {
    id: draft.id,
    title: draft.title,
    stageLabel: draft.stageLabel,
    updatedAt: draft.updatedAt,
  };
}

function updateDraftSummaryList(drafts: DraftSummary[], draft: DraftDocument) {
  const summary = buildDraftSummary(draft);
  const existing = drafts.some((entry) => entry.id === draft.id);
  if (!existing) return [summary, ...drafts];
  return drafts.map((entry) => (entry.id === draft.id ? summary : entry));
}

function detectSuggestionMode(
  body: string,
  selection: EditorTextRange,
): SuggestionMode | null {
  const [start, end] = selection;
  if (start !== end) return null;

  const before = body.slice(0, end);
  const lastChar = before.at(-1) ?? "";
  if (/[\n.!؟،؛]/u.test(lastChar)) return "sentence";
  return /[\p{L}\p{M}]{2,}$/u.test(before) ? "word" : null;
}

function toAnchorRect(rect: DOMRect | null): AnchorRect | null {
  if (!rect) return null;
  return {
    top: rect.top,
    left: rect.left,
    width: rect.width,
    height: rect.height,
  };
}

export function useEditorController() {
  const api = useEditorApi();
  const queryClient = useQueryClient();
  const [activeDraftId, setActiveDraftId] = useState("");
  const [activeFilter, setActiveFilter] = useState<FilterValue>("spelling");
  const [expandedCorrectionId, setExpandedCorrectionId] = useState<
    string | null
  >(null);
  const [focusedCorrectionId, setFocusedCorrectionId] = useState<string | null>(
    null,
  );
  const [navigationOpen, setNavigationOpen] = useState(false);
  const [correctionsOpen, setCorrectionsOpen] = useState(false);
  const [selection, setSelection] = useState<EditorTextRange>([0, 0]);
  const [anchorRect, setAnchorRect] = useState<AnchorRect | null>(null);
  const [draft, setDraft] = useState<DraftDocument | null>(null);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [analysisState, setAnalysisState] = useState<AnalysisState>("idle");
  const [saveError, setSaveError] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [suggestionsEnabled, setSuggestionsEnabled] = useState(true);
  const [suggestionState, setSuggestionState] = useState<SuggestionState>(
    defaultSuggestionState,
  );

  const draftRef = useRef<DraftDocument | null>(null);
  const selectionRef = useRef<EditorTextRange>([0, 0]);
  const saveTimerRef = useRef<number | null>(null);
  const analyzeTimerRef = useRef<number | null>(null);
  const suggestionTimerRef = useRef<number | null>(null);
  const saveAbortRef = useRef<AbortController | null>(null);
  const analyzeAbortRef = useRef<AbortController | null>(null);
  const suggestionAbortRef = useRef<AbortController | null>(null);
  const saveTicketRef = useRef(0);
  const analyzeTicketRef = useRef(0);
  const suggestionTicketRef = useRef(0);

  useEffect(() => {
    draftRef.current = draft;
  }, [draft]);

  useEffect(() => {
    selectionRef.current = selection;
  }, [selection]);

  const draftsQuery = useQuery({
    queryKey: editorQueryKeys.drafts,
    queryFn: ({ signal }) => api.listDrafts(signal),
  });

  useEffect(() => {
    if (activeDraftId || !draftsQuery.data?.length) return;
    const firstId = draftsQuery.data[0]?.id ?? "";
    const timer = setTimeout(() => {
      setActiveDraftId(firstId);
    }, 0);
    return () => clearTimeout(timer);
  }, [activeDraftId, draftsQuery.data]);

  const activeDraftQuery = useQuery({
    enabled: activeDraftId.length > 0,
    queryKey: editorQueryKeys.draft(activeDraftId),
    queryFn: ({ signal }) => api.getDraft(activeDraftId, signal),
  });

  const loadDraft = (nextDraft: DraftDocument) => {
    setDraft(cloneDraftDocument(nextDraft));
    setSelection([0, 0]);
    setExpandedCorrectionId(null);
    setFocusedCorrectionId(null);
    setSaveState("idle");
    setAnalysisState(nextDraft.corrections.length > 0 ? "ready" : "idle");
    setSaveError(null);
    setAnalysisError(null);
    setSuggestionState(defaultSuggestionState());
  };

  useEffect(() => {
    if (!activeDraftQuery.data) return;
    if (draftRef.current?.id === activeDraftQuery.data.id) return;
    loadDraft(activeDraftQuery.data);
  }, [activeDraftQuery.data]);

  const addDraftMutation = useMutation({
    mutationFn: ({ signal }: { signal?: AbortSignal }) =>
      api.createDraft(
        {
          title: DEFAULT_DRAFT_TITLE,
          body: DEFAULT_DRAFT_BODY,
        },
        signal,
      ),
    onSuccess: (createdDraft) => {
      queryClient.setQueryData<DraftSummary[]>(
        editorQueryKeys.drafts,
        (current = []) => [buildDraftSummary(createdDraft), ...current],
      );
      queryClient.setQueryData(
        editorQueryKeys.draft(createdDraft.id),
        createdDraft,
      );
      setActiveDraftId(createdDraft.id);
    },
  });

  const saveDraftMutation = useMutation({
    mutationFn: ({
      snapshot,
      signal,
    }: {
      snapshot: DraftDocument;
      signal: AbortSignal;
    }) =>
      api.updateDraft(
        snapshot.id,
        {
          title: snapshot.title,
          body: snapshot.body,
          clientRevision: snapshot.revision,
        },
        signal,
      ),
  });

  const analyzeDraftMutation = useMutation({
    mutationFn: ({
      snapshot,
      selectionSnapshot,
      signal,
    }: {
      snapshot: DraftDocument;
      selectionSnapshot: EditorTextRange;
      signal: AbortSignal;
    }) =>
      api.analyzeDraft(
        snapshot.id,
        {
          body: snapshot.body,
          selection: rangeToSelection(selectionSnapshot),
          caret: selectionSnapshot[1],
          clientRevision: snapshot.revision,
          categories: ["spelling", "grammar", "style"],
        },
        signal,
      ),
  });

  const suggestionMutation = useMutation({
    mutationFn: ({
      snapshot,
      selectionSnapshot,
      mode,
      signal,
    }: {
      snapshot: DraftDocument;
      selectionSnapshot: EditorTextRange;
      mode: SuggestionMode;
      signal: AbortSignal;
    }) =>
      api.getSuggestions(
        snapshot.id,
        {
          body: snapshot.body,
          selection: rangeToSelection(selectionSnapshot),
          caret: selectionSnapshot[1],
          clientRevision: snapshot.revision,
          mode,
          limit: 3,
        },
        signal,
      ),
  });

  const acceptCorrectionMutation = useMutation({
    mutationFn: ({
      draftId,
      correctionId,
      revision,
      body,
      signal,
    }: {
      draftId: string;
      correctionId: string;
      revision: number;
      body: string;
      signal?: AbortSignal;
    }) =>
      api.acceptCorrection(
        draftId,
        correctionId,
        { body, clientRevision: revision },
        signal,
      ),
  });

  const ignoreCorrectionMutation = useMutation({
    mutationFn: ({
      draftId,
      correctionId,
      revision,
      signal,
    }: {
      draftId: string;
      correctionId: string;
      revision: number;
      signal?: AbortSignal;
    }) =>
      api.ignoreCorrection(
        draftId,
        correctionId,
        { clientRevision: revision },
        signal,
      ),
  });

  const tashkeelMutation = useMutation({
    mutationFn: ({
      draftId,
      revision,
      body,
      selectionSnapshot,
      signal,
    }: {
      draftId: string;
      revision: number;
      body: string;
      selectionSnapshot: EditorTextRange;
      signal?: AbortSignal;
    }) =>
      api.applyTashkeel(
        draftId,
        {
          body,
          selection: rangeToSelection(selectionSnapshot),
          clientRevision: revision,
        },
        signal,
      ),
  });

  const syncDraftCaches = (nextDraft: DraftDocument) => {
    queryClient.setQueryData(editorQueryKeys.draft(nextDraft.id), nextDraft);
    queryClient.setQueryData<DraftSummary[]>(
      editorQueryKeys.drafts,
      (current = []) => updateDraftSummaryList(current, nextDraft),
    );
  };

  const hydrateLatestDraft = (latestDraft: DraftDocument) => {
    syncDraftCaches(latestDraft);
    loadDraft(latestDraft);
  };

  const closeSuggestions = () => {
    suggestionAbortRef.current?.abort();
    if (suggestionTimerRef.current) {
      window.clearTimeout(suggestionTimerRef.current);
      suggestionTimerRef.current = null;
    }
    setSuggestionState(defaultSuggestionState());
  };

  const scheduleSave = () => {
    if (saveTimerRef.current) window.clearTimeout(saveTimerRef.current);
    saveTimerRef.current = window.setTimeout(() => {
      const snapshot = draftRef.current
        ? cloneDraftDocument(draftRef.current)
        : null;
      if (!snapshot) return;

      saveAbortRef.current?.abort();
      const controller = new AbortController();
      saveAbortRef.current = controller;
      const ticket = ++saveTicketRef.current;
      setSaveState("saving");
      setSaveError(null);

      saveDraftMutation.mutate(
        { snapshot, signal: controller.signal },
        {
          onSuccess: (response, variables) => {
            if (ticket !== saveTicketRef.current) return;
            syncDraftCaches(response.draft);
            setDraft((current) => {
              if (!current || current.id !== variables.snapshot.id)
                return current;
              if (
                current.body === variables.snapshot.body &&
                current.title === variables.snapshot.title
              ) {
                return cloneDraftDocument(response.draft);
              }
              return {
                ...current,
                revision: response.persistedRevision,
                savedAt: response.savedAt,
              };
            });
            setSaveState("saved");
          },
          onError: (error) => {
            if (controller.signal.aborted) return;
            if (isRevisionConflict(error)) {
              const latestDraft = extractLatestDraft(error);
              if (latestDraft) hydrateLatestDraft(latestDraft);
            }
            setSaveState("error");
            setSaveError("تعذر حفظ التغييرات. أعد المحاولة.");
          },
        },
      );
    }, 800);
  };

  const scheduleAnalysis = () => {
    if (analyzeTimerRef.current) window.clearTimeout(analyzeTimerRef.current);
    analyzeTimerRef.current = window.setTimeout(() => {
      const snapshot = draftRef.current
        ? cloneDraftDocument(draftRef.current)
        : null;
      const selectionSnapshot = [...selectionRef.current] as EditorTextRange;
      if (!snapshot) return;

      analyzeAbortRef.current?.abort();
      const controller = new AbortController();
      analyzeAbortRef.current = controller;
      const ticket = ++analyzeTicketRef.current;
      setAnalysisState("loading");
      setAnalysisError(null);

      analyzeDraftMutation.mutate(
        { snapshot, selectionSnapshot, signal: controller.signal },
        {
          onSuccess: (response, variables) => {
            if (ticket !== analyzeTicketRef.current) return;
            setDraft((current) => {
              if (!current || current.id !== variables.snapshot.id)
                return current;
              if (current.body !== variables.snapshot.body) return current;
              return { ...current, corrections: response.corrections };
            });
            setAnalysisState("ready");
          },
          onError: (error) => {
            if (controller.signal.aborted) return;
            if (isRevisionConflict(error)) {
              const latestDraft = extractLatestDraft(error);
              if (latestDraft) hydrateLatestDraft(latestDraft);
            }
            setAnalysisState("error");
            setAnalysisError("تعذر تحديث الملاحظات الآن.");
          },
        },
      );
    }, 700);
  };

  const requestSuggestions = (
    mode: SuggestionMode,
    options?: {
      snapshot?: DraftDocument;
      selectionSnapshot?: EditorTextRange;
      delay?: number;
    },
  ) => {
    if (!suggestionsEnabled) return;

    const snapshot = options?.snapshot ?? draftRef.current;
    const selectionSnapshot =
      options?.selectionSnapshot ?? selectionRef.current;
    if (!snapshot) return;

    suggestionAbortRef.current?.abort();
    if (suggestionTimerRef.current)
      window.clearTimeout(suggestionTimerRef.current);

    const controller = new AbortController();
    suggestionAbortRef.current = controller;
    const ticket = ++suggestionTicketRef.current;
    setSuggestionState((current) => ({
      ...current,
      status: "loading",
      mode,
      errorMessage: null,
      isOpen: current.isOpen && current.mode === mode,
    }));

    suggestionTimerRef.current = window.setTimeout(
      () => {
        suggestionMutation.mutate(
          {
            snapshot: cloneDraftDocument(snapshot),
            selectionSnapshot: [...selectionSnapshot] as EditorTextRange,
            mode,
            signal: controller.signal,
          },
          {
            onSuccess: (response, variables) => {
              if (ticket !== suggestionTicketRef.current) return;
              const current = draftRef.current;
              if (!current || current.id !== variables.snapshot.id) return;
              if (current.body !== variables.snapshot.body) return;
              if (
                selectionRef.current[0] !== variables.selectionSnapshot[0] ||
                selectionRef.current[1] !== variables.selectionSnapshot[1]
              ) {
                return;
              }
              setSuggestionState({
                status: "ready",
                isOpen: response.suggestions.length > 0,
                mode: response.mode,
                highlightedIndex: 0,
                replaceRange: response.replaceRange,
                suggestions: response.suggestions,
                sessionId: response.suggestionSessionId,
                errorMessage: null,
              });
            },
            onError: (error) => {
              if (controller.signal.aborted) return;
              if (isRevisionConflict(error)) {
                const latestDraft = extractLatestDraft(error);
                if (latestDraft) hydrateLatestDraft(latestDraft);
              }
              setSuggestionState({
                ...defaultSuggestionState(),
                status: "error",
                errorMessage: "تعذر تحميل الاقتراحات.",
              });
            },
          },
        );
      },
      options?.delay ?? (mode === "word" ? 180 : 350),
    );
  };

  const updateLocalDraft = (
    updater: (current: DraftDocument) => DraftDocument,
    options?: {
      scheduleSave?: boolean;
      scheduleAnalysis?: boolean;
      closeSuggestions?: boolean;
    },
  ) => {
    setDraft((current) => {
      if (!current) return current;
      return updater(current);
    });

    if (options?.closeSuggestions !== false) {
      closeSuggestions();
    }

    if (options?.scheduleSave) {
      setSaveState("idle");
      scheduleSave();
    }

    if (options?.scheduleAnalysis) {
      setAnalysisState("idle");
      scheduleAnalysis();
    }
  };

  const updateTitle = (title: string) => {
    updateLocalDraft((current) => ({ ...current, title, updatedAt: "الآن" }), {
      scheduleSave: true,
    });
  };

  const updateBody = (body: string) => {
    updateLocalDraft(
      (current) => ({
        ...current,
        body,
        updatedAt: "الآن",
        formatting: reconcileFormatting(current.formatting, current.body, body),
        corrections: resolveCorrections(
          current.body,
          body,
          current.corrections,
        ),
      }),
      { scheduleSave: true, scheduleAnalysis: true },
    );
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      if (!draft || !suggestionsEnabled) {
        closeSuggestions();
        return;
      }

      const mode = detectSuggestionMode(draft.body, selection);
      if (!mode) {
        closeSuggestions();
        return;
      }

      requestSuggestions(mode, {
        snapshot: draft,
        selectionSnapshot: selection,
      });
    }, 0);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draft?.body, draft?.id, draft?.revision, selection, suggestionsEnabled]);

  useEffect(
    () => () => {
      saveAbortRef.current?.abort();
      analyzeAbortRef.current?.abort();
      suggestionAbortRef.current?.abort();
      if (saveTimerRef.current) window.clearTimeout(saveTimerRef.current);
      if (analyzeTimerRef.current) window.clearTimeout(analyzeTimerRef.current);
      if (suggestionTimerRef.current) {
        window.clearTimeout(suggestionTimerRef.current);
      }
    },
    [],
  );

  const activeDraft = draft;
  const correctionCounts: CorrectionCounts = useMemo(
    () => getCorrectionCounts(activeDraft?.corrections ?? []),
    [activeDraft?.corrections],
  );

  const visibleCorrections: Correction[] = useMemo(() => {
    return (activeDraft?.corrections ?? []).filter((correction) => {
      if (correction.status === "accepted" || correction.status === "ignored") {
        return false;
      }
      return correction.category === activeFilter;
    });
  }, [activeDraft?.corrections, activeFilter]);

  const selectDraft = (draftId: string) => {
    setActiveDraftId(draftId);
    setNavigationOpen(false);
  };

  const focusCorrection = (correctionId: string | null) => {
    setFocusedCorrectionId(correctionId);
  };

  const toggleExpanded = (correctionId: string) => {
    setExpandedCorrectionId((current) =>
      current === correctionId ? null : correctionId,
    );
    setFocusedCorrectionId(correctionId);
  };

  const acceptCorrection = (correctionId: string) => {
    const snapshot = draftRef.current;
    if (!snapshot) return;

    acceptCorrectionMutation.mutate(
      {
        draftId: snapshot.id,
        correctionId,
        revision: snapshot.revision,
        body: snapshot.body,
      },
      {
        onSuccess: (response) => {
          setDraft((current) => {
            if (!current || current.id !== snapshot.id) return current;
            const nextDraft = {
              ...current,
              body: response.draftBody,
              revision: response.persistedRevision,
              corrections: response.corrections,
              updatedAt: "الآن",
            };
            syncDraftCaches(nextDraft);
            return nextDraft;
          });
          setExpandedCorrectionId(null);
          setFocusedCorrectionId(null);
          setSaveState("saved");
          setAnalysisState("ready");
        },
        onError: (error) => {
          if (isRevisionConflict(error)) {
            const latestDraft = extractLatestDraft(error);
            if (latestDraft) hydrateLatestDraft(latestDraft);
          }
        },
      },
    );
  };

  const ignoreCorrection = (correctionId: string) => {
    const snapshot = draftRef.current;
    if (!snapshot) return;

    ignoreCorrectionMutation.mutate(
      {
        draftId: snapshot.id,
        correctionId,
        revision: snapshot.revision,
      },
      {
        onSuccess: (response) => {
          setDraft((current) => {
            if (!current || current.id !== snapshot.id) return current;
            const nextDraft = {
              ...current,
              revision: current.revision + 1,
              corrections: response.corrections,
              updatedAt: "الآن",
            };
            syncDraftCaches(nextDraft);
            return nextDraft;
          });
          setExpandedCorrectionId(null);
          setFocusedCorrectionId(null);
          setSaveState("saved");
          setAnalysisState("ready");
        },
      },
    );
  };

  const toggleStrong = (range: EditorTextRange) => {
    updateLocalDraft(
      (current) => {
        const resolved = resolveFormattingRange(current.body, range);
        return {
          ...current,
          formatting: {
            ...current.formatting,
            strong: toggleRange(current.formatting.strong, resolved),
          },
        };
      },
      { closeSuggestions: false },
    );
  };

  const toggleEmphasis = (range: EditorTextRange) => {
    updateLocalDraft(
      (current) => {
        const resolved = resolveFormattingRange(current.body, range);
        return {
          ...current,
          formatting: {
            ...current.formatting,
            emphasis: toggleRange(current.formatting.emphasis, resolved),
          },
        };
      },
      { closeSuggestions: false },
    );
  };

  const cycleList = (range: EditorTextRange) => {
    updateLocalDraft(
      (current) => {
        const firstLine = getSelectedLineIndices(current.body, range)[0] ?? 0;
        const nextList = cycleListStyle(
          getLineFormat(current.formatting, firstLine).list,
        );
        return {
          ...current,
          formatting: {
            ...current.formatting,
            lines: updateLineFormats(current, range, (format) => ({
              ...format,
              list: nextList,
            })),
          },
        };
      },
      { closeSuggestions: false },
    );
  };

  const setAlign = (
    range: EditorTextRange,
    align: EditorLineFormat["align"],
  ) => {
    updateLocalDraft(
      (current) => ({
        ...current,
        formatting: {
          ...current.formatting,
          lines: updateLineFormats(current, range, (format) => ({
            ...format,
            align,
          })),
        },
      }),
      { closeSuggestions: false },
    );
  };

  const applyTashkeel = () => {
    const snapshot = draftRef.current;
    const selectionSnapshot = [...selectionRef.current] as EditorTextRange;
    if (!snapshot) return;

    tashkeelMutation.mutate(
      {
        draftId: snapshot.id,
        revision: snapshot.revision,
        body: snapshot.body,
        selectionSnapshot,
      },
      {
        onSuccess: (response) => {
          setDraft((current) => {
            if (!current || current.id !== snapshot.id) return current;
            const nextDraft = {
              ...current,
              body: response.draftBody,
              revision: response.persistedRevision,
              updatedAt: "الآن",
            };
            syncDraftCaches(nextDraft);
            return nextDraft;
          });
          setSaveState("saved");
          scheduleAnalysis();
        },
        onError: (error) => {
          if (isRevisionConflict(error)) {
            const latestDraft = extractLatestDraft(error);
            if (latestDraft) {
              hydrateLatestDraft(latestDraft);
              return;
            }
          }

          const localResult = applyTashkeelToBody(
            snapshot.body,
            selectionSnapshot,
          );
          if (localResult.applied) {
            updateBody(localResult.body);
          }
        },
      },
    );
  };

  const requestSentenceSuggestions = () => {
    const snapshot = draftRef.current;
    if (!snapshot || !suggestionsEnabled) return;
    requestSuggestions("sentence", {
      snapshot,
      selectionSnapshot: selectionRef.current,
      delay: 0,
    });
  };

  const cycleSuggestion = (direction: 1 | -1) => {
    setSuggestionState((current) => {
      if (!current.isOpen || current.suggestions.length === 0) return current;
      const nextIndex =
        (current.highlightedIndex + direction + current.suggestions.length) %
        current.suggestions.length;
      return { ...current, highlightedIndex: nextIndex };
    });
  };

  const applySuggestion = (index = suggestionState.highlightedIndex) => {
    const snapshot = draftRef.current;
    if (!snapshot || !suggestionState.replaceRange) return;

    const suggestion = suggestionState.suggestions[index];
    if (!suggestion) return;

    const nextBody = replaceTextRange(
      snapshot.body,
      suggestionState.replaceRange,
      suggestion.insertText,
    );
    const nextCaret =
      suggestionState.replaceRange.start + suggestion.insertText.length;

    updateLocalDraft(
      (current) => ({
        ...current,
        body: nextBody,
        updatedAt: "الآن",
      }),
      { scheduleSave: true, scheduleAnalysis: true, closeSuggestions: true },
    );
    setSelection([nextCaret, nextCaret]);
  };

  const toggleSuggestionsEnabled = () => {
    setSuggestionsEnabled((current) => {
      const next = !current;
      if (!next) closeSuggestions();
      return next;
    });
  };

  return {
    drafts: draftsQuery.data ?? [],
    draftsLoading: draftsQuery.isPending,
    activeDraft,
    activeDraftId,
    activeFilter,
    expandedCorrectionId,
    focusedCorrectionId,
    navigationOpen,
    correctionsOpen,
    selection,
    correctionCounts,
    visibleCorrections,
    saveState,
    analysisState,
    saveError,
    analysisError,
    suggestionsEnabled,
    suggestionState,
    suggestionAnchorRect: anchorRect,
    isHydratingDraft: activeDraftQuery.isPending && !activeDraft,
    selectDraft,
    addDraft: () => addDraftMutation.mutate({}),
    updateTitle,
    updateBody,
    updateSelection: setSelection,
    setSuggestionAnchorRect: (rect: DOMRect | null) =>
      setAnchorRect(toAnchorRect(rect)),
    setFilter: setActiveFilter,
    toggleExpanded,
    focusCorrection,
    acceptCorrection,
    ignoreCorrection,
    togglePanel: (panel: EditorPanel) =>
      panel === "navigation"
        ? setNavigationOpen((open) => !open)
        : setCorrectionsOpen((open) => !open),
    closePanel: (panel: EditorPanel) =>
      panel === "navigation"
        ? setNavigationOpen(false)
        : setCorrectionsOpen(false),
    toggleStrong,
    toggleEmphasis,
    applyTashkeel,
    cycleList,
    setAlign,
    toggleSuggestionsEnabled,
    requestSentenceSuggestions,
    cycleSuggestion,
    highlightSuggestion: (index: number) =>
      setSuggestionState((current) => ({
        ...current,
        highlightedIndex: index,
      })),
    applySuggestion,
    closeSuggestions,
  };
}

export {
  getLineFormat,
  getSelectedLineIndices,
  isRangeCovered,
  resolveFormattingRange,
};
