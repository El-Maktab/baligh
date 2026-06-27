export type CorrectionCategory = "spelling" | "grammar" | "style";

export type CorrectionStatus = "active" | "accepted" | "ignored" | "stale";

export type EditorListStyle = "none" | "bullet" | "numbered";

export type EditorTextRange = [start: number, end: number];

export type EditorSelection = {
  start: number;
  end: number;
};

export type DraftRevision = number;

export type EditorLineFormat = {
  list: EditorListStyle;
  align: "start" | "center" | "end";
};

export type EditorFormatting = {
  strong: EditorTextRange[];
  emphasis: EditorTextRange[];
  lines: Record<number, EditorLineFormat>;
};

export type TashkeelResult = {
  body: string;
  applied: boolean;
};

export type FindingKind = "correction" | "detection";

type FindingBase = {
  id: string;
  kind: FindingKind;
  actionable: boolean;
  category: CorrectionCategory;
  bucket: CorrectionCategory;
  status: CorrectionStatus;
  span: EditorSelection;
  title: string;
  lineLabel: string;
  original: string;
  explanation: string;
  ruleLabel: string;
  taxonomyCode: string;
  taxonomyLabel: string;
  sourceModule: string;
  confidence?: number;
  tokenRefs?: number[];
  alternatives?: string[];
};

export type CorrectionFinding = FindingBase & {
  kind: "correction";
  actionable: true;
  replacement: string;
};

export type DetectionFinding = FindingBase & {
  kind: "detection";
  actionable: false;
  replacement: null;
};

export type EditorFinding = CorrectionFinding | DetectionFinding;
export type Correction = EditorFinding;

export type CorrectionCounts = Record<CorrectionCategory | "all", number>;

export type SuggestionMode = "word" | "sentence";

export type SuggestionItem = {
  id: string;
  label: string;
  insertText: string;
  displayText: string;
  kind: SuggestionMode;
};

export type SuggestionResponse = {
  suggestionSessionId: string;
  mode: SuggestionMode;
  replaceRange: EditorSelection;
  suggestions: SuggestionItem[];
};

export type DraftSummary = {
  id: string;
  title: string;
  stageLabel: string;
  updatedAt: string;
};

export type DraftDocument = DraftSummary & {
  body: string;
  revision: DraftRevision;
  savedAt?: string;
  formatting: EditorFormatting;
  corrections: Correction[];
};

export type EditorDraft = DraftDocument;

export type SaveState = "idle" | "saving" | "saved" | "error";

export type AnalysisState = "idle" | "loading" | "ready" | "error";

export type DraftUpdatePayload = {
  title?: string;
  body?: string;
  formatting?: EditorFormatting;
  clientRevision: DraftRevision;
};

export type DraftUpdateResponse = {
  draft: DraftDocument;
  persistedRevision: DraftRevision;
  savedAt: string;
};

export type AnalyzeDraftPayload = {
  body: string;
  selection: EditorSelection;
  caret: number;
  clientRevision: DraftRevision;
  categories: CorrectionCategory[];
};

export type AnalyzeDraftResponse = {
  analysisRevision: DraftRevision;
  corrections: Correction[];
  counts: CorrectionCounts;
};

export type CorrectionActionPayload = {
  body?: string;
  clientRevision: DraftRevision;
};

export type AcceptCorrectionResponse = {
  draftBody: string;
  persistedRevision: DraftRevision;
  corrections: Correction[];
  counts: CorrectionCounts;
};

export type IgnoreCorrectionResponse = {
  correctionId: string;
  status: CorrectionStatus;
  corrections: Correction[];
  counts: CorrectionCounts;
};

export type SuggestionRequest = {
  body: string;
  selection: EditorSelection;
  caret: number;
  clientRevision: DraftRevision;
  mode: SuggestionMode;
  limit: number;
};

export type TashkeelRequest = {
  body: string;
  selection: EditorSelection;
  clientRevision: DraftRevision;
};

export type TashkeelResponse = {
  draftBody: string;
  replaceRange: EditorSelection;
  persistedRevision: DraftRevision;
};
