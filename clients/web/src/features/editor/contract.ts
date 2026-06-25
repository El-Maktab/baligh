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

export const editorContract = {
  drafts: "/api/v1/drafts",
  draft: (draftId: string) => `/api/v1/drafts/${draftId}`,
  analyze: (draftId: string) => `/api/v1/drafts/${draftId}/analyze`,
  acceptCorrection: (draftId: string, correctionId: string) =>
    `/api/v1/drafts/${draftId}/corrections/${correctionId}/accept`,
  ignoreCorrection: (draftId: string, correctionId: string) =>
    `/api/v1/drafts/${draftId}/corrections/${correctionId}/ignore`,
  suggestions: (draftId: string) => `/api/v1/drafts/${draftId}/suggestions`,
  tashkeel: (draftId: string) => `/api/v1/drafts/${draftId}/tashkeel`,
} as const;

export type EditorContract = {
  DraftSummary: DraftSummary;
  DraftDocument: DraftDocument;
  DraftUpdatePayload: DraftUpdatePayload;
  DraftUpdateResponse: DraftUpdateResponse;
  AnalyzeDraftPayload: AnalyzeDraftPayload;
  AnalyzeDraftResponse: AnalyzeDraftResponse;
  CorrectionActionPayload: CorrectionActionPayload;
  AcceptCorrectionResponse: AcceptCorrectionResponse;
  IgnoreCorrectionResponse: IgnoreCorrectionResponse;
  SuggestionRequest: SuggestionRequest;
  SuggestionResponse: SuggestionResponse;
  TashkeelRequest: TashkeelRequest;
  TashkeelResponse: TashkeelResponse;
};
