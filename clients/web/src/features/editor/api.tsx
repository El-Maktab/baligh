import {
  createContext,
  useContext,
  type PropsWithChildren,
} from "react";

import { BLANK_DRAFT_BODY, SEEDED_DRAFTS } from "./mockData";
import {
  applyTashkeelToBody,
  cloneDraftDocument,
  getCorrectionCounts,
  replaceTextRange,
  resolveCorrections,
  selectionToRange,
} from "./editorState";
import { editorContract } from "./contract";
import type {
  AcceptCorrectionResponse,
  AnalyzeDraftPayload,
  AnalyzeDraftResponse,
  CorrectionActionPayload,
  DraftDocument,
  DraftSummary,
  DraftUpdatePayload,
  DraftUpdateResponse,
  IgnoreCorrectionResponse,
  SuggestionRequest,
  SuggestionResponse,
  TashkeelRequest,
  TashkeelResponse,
} from "./types";
import type { EditorDataSource } from "../../app/environment";

export class EditorApiError extends Error {
  status: number;
  payload?: unknown;

  constructor(message: string, status: number, payload?: unknown) {
    super(message);
    this.name = "EditorApiError";
    this.status = status;
    this.payload = payload;
  }
}

export type EditorApi = {
  listDrafts: (signal?: AbortSignal) => Promise<DraftSummary[]>;
  createDraft: (
    payload: { title?: string; body?: string },
    signal?: AbortSignal,
  ) => Promise<DraftDocument>;
  getDraft: (draftId: string, signal?: AbortSignal) => Promise<DraftDocument>;
  updateDraft: (
    draftId: string,
    payload: DraftUpdatePayload,
    signal?: AbortSignal,
  ) => Promise<DraftUpdateResponse>;
  analyzeDraft: (
    draftId: string,
    payload: AnalyzeDraftPayload,
    signal?: AbortSignal,
  ) => Promise<AnalyzeDraftResponse>;
  acceptCorrection: (
    draftId: string,
    correctionId: string,
    payload: CorrectionActionPayload,
    signal?: AbortSignal,
  ) => Promise<AcceptCorrectionResponse>;
  ignoreCorrection: (
    draftId: string,
    correctionId: string,
    payload: CorrectionActionPayload,
    signal?: AbortSignal,
  ) => Promise<IgnoreCorrectionResponse>;
  getSuggestions: (
    draftId: string,
    payload: SuggestionRequest,
    signal?: AbortSignal,
  ) => Promise<SuggestionResponse>;
  applyTashkeel: (
    draftId: string,
    payload: TashkeelRequest,
    signal?: AbortSignal,
  ) => Promise<TashkeelResponse>;
};

type StoredDraft = DraftDocument;

const EditorApiContext = createContext<EditorApi | null>(null);

function delay(signal?: AbortSignal, ms = 10) {
  return new Promise<void>((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException("The request was aborted", "AbortError"));
      return;
    }
    const timeoutId = window.setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        window.clearTimeout(timeoutId);
        reject(new DOMException("The request was aborted", "AbortError"));
      },
      { once: true },
    );
  });
}

function summarizeDraft(draft: DraftDocument): DraftSummary {
  return {
    id: draft.id,
    title: draft.title,
    stageLabel: draft.stageLabel,
    updatedAt: draft.updatedAt,
  };
}

function cloneStoredDraft(draft: StoredDraft) {
  return cloneDraftDocument(draft);
}

function assertRevision(draft: StoredDraft, clientRevision: number) {
  if (clientRevision !== draft.revision) {
    throw new EditorApiError("Revision conflict", 409, {
      latestDraft: cloneStoredDraft(draft),
    });
  }
}

function createWordSuggestions(prefix: string) {
  const dictionary = [
    "المحبة",
    "المحرر",
    "المراجعة",
    "المعنى",
    "الصفحة",
    "الفريق",
    "الصياغة",
  ];
  const matches = dictionary.filter((entry) => entry.startsWith(prefix));
  return matches.length > 0 ? matches : [prefix + "ة", prefix + "ات"];
}

function buildSuggestions(payload: SuggestionRequest): SuggestionResponse {
  const beforeCaret = payload.body.slice(0, payload.caret);
  const afterCaret = payload.body.slice(payload.caret);
  const wordMatch = beforeCaret.match(/[\p{L}\p{M}]+$/u);

  if (payload.mode === "word" && wordMatch) {
    const prefix = wordMatch[0];
    const start = payload.caret - prefix.length;
    const suffixMatch = afterCaret.match(/^[\p{L}\p{M}]*/u);
    const suffix = suffixMatch?.[0] ?? "";
    return {
      suggestionSessionId: `suggest-${Date.now()}`,
      mode: "word",
      replaceRange: { start, end: payload.caret + suffix.length },
      suggestions: createWordSuggestions(prefix)
        .slice(0, payload.limit)
        .map((entry, index) => ({
          id: `word-${index}`,
          label: entry,
          displayText: entry,
          insertText: entry,
          kind: "word" as const,
        })),
    };
  }

  const continuations = [
    " لذلك أراجع الصياغة قبل الإرسال.",
    " ثم أعود لتنقيح الجملة التالية.",
    " وهذا يمنح النص إيقاعاً أوضح.",
  ];

  return {
    suggestionSessionId: `suggest-${Date.now()}`,
    mode: "sentence",
    replaceRange: { start: payload.caret, end: payload.caret },
    suggestions: continuations.slice(0, payload.limit).map((entry, index) => ({
      id: `sentence-${index}`,
      label: entry.trim(),
      displayText: entry,
      insertText: entry,
      kind: "sentence",
    })),
  };
}

export function createMockEditorApi(
  initialDrafts: DraftDocument[] = SEEDED_DRAFTS,
): EditorApi {
  let nextDraftNumber = initialDrafts.length + 1;
  const drafts = new Map<string, StoredDraft>(
    initialDrafts.map((draft) => [draft.id, cloneStoredDraft(draft)]),
  );

  const getStoredDraft = (draftId: string) => {
    const draft = drafts.get(draftId);
    if (!draft) throw new EditorApiError("Draft not found", 404);
    return draft;
  };

  return {
    async listDrafts(signal?: AbortSignal) {
      await delay(signal);
      return [...drafts.values()].map((draft) => summarizeDraft(draft));
    },
    async createDraft(
      payload: { title?: string; body?: string },
      signal?: AbortSignal,
    ) {
      await delay(signal);
      const draft: StoredDraft = {
        id: `draft-${nextDraftNumber}`,
        title: payload.title ?? `نص جديد ${nextDraftNumber}`,
        body: payload.body ?? BLANK_DRAFT_BODY,
        stageLabel: "جاهز للربط",
        updatedAt: "الآن",
        savedAt: new Date().toISOString(),
        revision: 1,
        formatting: { strong: [], emphasis: [], lines: {} },
        corrections: [],
      };
      nextDraftNumber += 1;
      drafts.set(draft.id, draft);
      return cloneStoredDraft(draft);
    },
    async getDraft(draftId: string, signal?: AbortSignal) {
      await delay(signal);
      return cloneStoredDraft(getStoredDraft(draftId));
    },
    async updateDraft(
      draftId: string,
      payload: DraftUpdatePayload,
      signal?: AbortSignal,
    ) {
      await delay(signal);
      const draft = getStoredDraft(draftId);
      assertRevision(draft, payload.clientRevision);

      const nextBody = payload.body ?? draft.body;
      const nextTitle = payload.title ?? draft.title;
      draft.corrections = resolveCorrections(draft.body, nextBody, draft.corrections);
      draft.body = nextBody;
      draft.title = nextTitle;
      draft.updatedAt = "الآن";
      draft.savedAt = new Date().toISOString();
      draft.revision += 1;

      return {
        draft: cloneStoredDraft(draft),
        persistedRevision: draft.revision,
        savedAt: draft.savedAt,
      };
    },
    async analyzeDraft(
      draftId: string,
      payload: AnalyzeDraftPayload,
      signal?: AbortSignal,
    ) {
      await delay(signal);
      const draft = getStoredDraft(draftId);
      assertRevision(draft, payload.clientRevision);
      draft.corrections = resolveCorrections(draft.body, payload.body, draft.corrections);
      if (draft.body !== payload.body) {
        draft.body = payload.body;
      }

      return {
        analysisRevision: draft.revision,
        corrections: cloneStoredDraft(draft).corrections,
        counts: getCorrectionCounts(draft.corrections),
      };
    },
    async acceptCorrection(
      draftId: string,
      correctionId: string,
      payload: CorrectionActionPayload,
      signal?: AbortSignal,
    ) {
      await delay(signal);
      const draft = getStoredDraft(draftId);
      assertRevision(draft, payload.clientRevision);

      const correction = draft.corrections.find((entry) => entry.id === correctionId);
      if (!correction || correction.status === "stale") {
        throw new EditorApiError("Correction not available", 409, {
          latestDraft: cloneStoredDraft(draft),
        });
      }

      const nextBody = payload.body ?? draft.body;
      if (draft.body !== nextBody) {
        draft.corrections = resolveCorrections(draft.body, nextBody, draft.corrections);
        draft.body = nextBody;
      }

      const refreshed = draft.corrections.find((entry) => entry.id === correctionId);
      if (!refreshed || draft.body.slice(refreshed.span.start, refreshed.span.end) !== refreshed.original) {
        throw new EditorApiError("Correction became stale", 409, {
          latestDraft: cloneStoredDraft(draft),
        });
      }

      const { start, end } = refreshed.span;
      const delta = refreshed.replacement.length - (end - start);
      draft.body = replaceTextRange(draft.body, refreshed.span, refreshed.replacement);
      draft.corrections = draft.corrections.map((entry) => {
        if (entry.id === correctionId) {
          return { ...entry, status: "accepted" as const };
        }
        if (entry.status === "active" && entry.span.start >= end) {
          return {
            ...entry,
            span: {
              start: entry.span.start + delta,
              end: entry.span.end + delta,
            },
          };
        }
        return entry;
      });
      draft.updatedAt = "الآن";
      draft.savedAt = new Date().toISOString();
      draft.revision += 1;

      return {
        draftBody: draft.body,
        persistedRevision: draft.revision,
        corrections: cloneStoredDraft(draft).corrections,
        counts: getCorrectionCounts(draft.corrections),
      };
    },
    async ignoreCorrection(
      draftId: string,
      correctionId: string,
      payload: CorrectionActionPayload,
      signal?: AbortSignal,
    ) {
      await delay(signal);
      const draft = getStoredDraft(draftId);
      assertRevision(draft, payload.clientRevision);
      draft.corrections = draft.corrections.map((entry) =>
        entry.id === correctionId ? { ...entry, status: "ignored" as const } : entry,
      );
      draft.updatedAt = "الآن";
      draft.savedAt = new Date().toISOString();
      draft.revision += 1;

      return {
        correctionId,
        status: "ignored",
        corrections: cloneStoredDraft(draft).corrections,
        counts: getCorrectionCounts(draft.corrections),
      };
    },
    async getSuggestions(_draftId, payload, signal) {
      await delay(signal);
      return buildSuggestions(payload);
    },
    async applyTashkeel(draftId, payload, signal) {
      await delay(signal);
      const draft = getStoredDraft(draftId);
      assertRevision(draft, payload.clientRevision);
      const range = selectionToRange(payload.selection);
      const nextRange = {
        start: Math.min(range[0], range[1]),
        end: Math.max(range[0], range[1]),
      };
      const result = applyTashkeelToBody(draft.body, range);
      if (result.applied) {
        draft.corrections = resolveCorrections(draft.body, result.body, draft.corrections);
        draft.body = result.body;
        draft.revision += 1;
        draft.updatedAt = "الآن";
        draft.savedAt = new Date().toISOString();
      }
      return {
        draftBody: draft.body,
        replaceRange: nextRange,
        persistedRevision: draft.revision,
      };
    },
  };
}

async function requestJson<TResponse>(
  baseUrl: string,
  path: string,
  init: RequestInit,
  signal?: AbortSignal,
) {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
    signal,
  });
  const data = (await response.json().catch(() => undefined)) as TResponse;
  if (!response.ok) {
    throw new EditorApiError(response.statusText, response.status, data);
  }
  return data;
}

function isFallbackWorthy(error: unknown) {
  if (error instanceof EditorApiError) {
    return error.status >= 500 || error.status === 0;
  }
  if (error instanceof TypeError) {
    return true;
  }
  if (error instanceof DOMException && error.name !== "AbortError") {
    return true;
  }
  return false;
}

export function createHttpEditorApi(baseUrl: string): EditorApi {
  return {
    listDrafts: (signal) =>
      requestJson<DraftSummary[]>(
        baseUrl,
        editorContract.drafts,
        { method: "GET" },
        signal,
      ),
    createDraft: (payload, signal) =>
      requestJson<DraftDocument>(
        baseUrl,
        editorContract.drafts,
        { method: "POST", body: JSON.stringify(payload) },
        signal,
      ),
    getDraft: (draftId, signal) =>
      requestJson<DraftDocument>(
        baseUrl,
        editorContract.draft(draftId),
        { method: "GET" },
        signal,
      ),
    updateDraft: (draftId, payload, signal) =>
      requestJson<DraftUpdateResponse>(
        baseUrl,
        editorContract.draft(draftId),
        { method: "PATCH", body: JSON.stringify(payload) },
        signal,
      ),
    analyzeDraft: (draftId, payload, signal) =>
      requestJson<AnalyzeDraftResponse>(
        baseUrl,
        editorContract.analyze(draftId),
        { method: "POST", body: JSON.stringify(payload) },
        signal,
      ),
    acceptCorrection: (draftId, correctionId, payload, signal) =>
      requestJson<AcceptCorrectionResponse>(
        baseUrl,
        editorContract.acceptCorrection(draftId, correctionId),
        { method: "POST", body: JSON.stringify(payload) },
        signal,
      ),
    ignoreCorrection: (draftId, correctionId, payload, signal) =>
      requestJson<IgnoreCorrectionResponse>(
        baseUrl,
        editorContract.ignoreCorrection(draftId, correctionId),
        { method: "POST", body: JSON.stringify(payload) },
        signal,
      ),
    getSuggestions: (draftId, payload, signal) =>
      requestJson<SuggestionResponse>(
        baseUrl,
        editorContract.suggestions(draftId),
        { method: "POST", body: JSON.stringify(payload) },
        signal,
      ),
    applyTashkeel: (draftId, payload, signal) =>
      requestJson<TashkeelResponse>(
        baseUrl,
        editorContract.tashkeel(draftId),
        { method: "POST", body: JSON.stringify(payload) },
        signal,
      ),
  };
}

export function createEditorApi(
  baseUrl: string | undefined,
  dataSource: EditorDataSource,
) {
  if (dataSource === "mock" || !baseUrl) {
    return createMockEditorApi();
  }

  const httpApi = createHttpEditorApi(baseUrl);
  if (dataSource === "api") {
    return httpApi;
  }

  const mockApi = createMockEditorApi();

  return {
    async listDrafts(signal?: AbortSignal) {
      try {
        return await httpApi.listDrafts(signal);
      } catch (error) {
        if (!isFallbackWorthy(error)) throw error;
        return mockApi.listDrafts(signal);
      }
    },
    async createDraft(
      payload: { title?: string; body?: string },
      signal?: AbortSignal,
    ) {
      try {
        return await httpApi.createDraft(payload, signal);
      } catch (error) {
        if (!isFallbackWorthy(error)) throw error;
        return mockApi.createDraft(payload, signal);
      }
    },
    async getDraft(draftId: string, signal?: AbortSignal) {
      try {
        return await httpApi.getDraft(draftId, signal);
      } catch (error) {
        if (!isFallbackWorthy(error)) throw error;
        return mockApi.getDraft(draftId, signal);
      }
    },
    async updateDraft(
      draftId: string,
      payload: DraftUpdatePayload,
      signal?: AbortSignal,
    ) {
      try {
        return await httpApi.updateDraft(draftId, payload, signal);
      } catch (error) {
        if (!isFallbackWorthy(error)) throw error;
        return mockApi.updateDraft(draftId, payload, signal);
      }
    },
    async analyzeDraft(
      draftId: string,
      payload: AnalyzeDraftPayload,
      signal?: AbortSignal,
    ) {
      try {
        return await httpApi.analyzeDraft(draftId, payload, signal);
      } catch (error) {
        if (!isFallbackWorthy(error)) throw error;
        return mockApi.analyzeDraft(draftId, payload, signal);
      }
    },
    async acceptCorrection(
      draftId: string,
      correctionId: string,
      payload: CorrectionActionPayload,
      signal?: AbortSignal,
    ) {
      try {
        return await httpApi.acceptCorrection(
          draftId,
          correctionId,
          payload,
          signal,
        );
      } catch (error) {
        if (!isFallbackWorthy(error)) throw error;
        return mockApi.acceptCorrection(draftId, correctionId, payload, signal);
      }
    },
    async ignoreCorrection(
      draftId: string,
      correctionId: string,
      payload: CorrectionActionPayload,
      signal?: AbortSignal,
    ) {
      try {
        return await httpApi.ignoreCorrection(
          draftId,
          correctionId,
          payload,
          signal,
        );
      } catch (error) {
        if (!isFallbackWorthy(error)) throw error;
        return mockApi.ignoreCorrection(draftId, correctionId, payload, signal);
      }
    },
    async getSuggestions(
      draftId: string,
      payload: SuggestionRequest,
      signal?: AbortSignal,
    ) {
      try {
        return await httpApi.getSuggestions(draftId, payload, signal);
      } catch (error) {
        if (!isFallbackWorthy(error)) throw error;
        return mockApi.getSuggestions(draftId, payload, signal);
      }
    },
    async applyTashkeel(
      draftId: string,
      payload: TashkeelRequest,
      signal?: AbortSignal,
    ) {
      try {
        return await httpApi.applyTashkeel(draftId, payload, signal);
      } catch (error) {
        if (!isFallbackWorthy(error)) throw error;
        return mockApi.applyTashkeel(draftId, payload, signal);
      }
    },
  };
}

export function EditorApiProvider({
  api,
  children,
}: PropsWithChildren<{ api: EditorApi }>) {
  return (
    <EditorApiContext.Provider value={api}>{children}</EditorApiContext.Provider>
  );
}

export function useEditorApi() {
  const api = useContext(EditorApiContext);
  if (!api) throw new Error("EditorApiProvider is required");
  return api;
}
