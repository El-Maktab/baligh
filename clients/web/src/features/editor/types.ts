export type CorrectionCategory = "spelling" | "grammar" | "style";

export type CorrectionStatus = "active" | "accepted" | "ignored" | "stale";

export type EditorListStyle = "none" | "bullet" | "numbered";

export type EditorTextRange = [start: number, end: number];

export type EditorLineFormat = {
  list: EditorListStyle;
  align: "start" | "center" | "end";
};

export type EditorFormatting = {
  strong: EditorTextRange[];
  emphasis: EditorTextRange[];
  lines: Record<number, EditorLineFormat>;
};

export type MockCorrection = {
  id: string;
  category: CorrectionCategory;
  status: CorrectionStatus;
  span: [start: number, end: number];
  title: string;
  lineLabel: string;
  original: string;
  replacement: string;
  explanation: string;
  ruleLabel: string;
};

export type EditorDraft = {
  id: string;
  title: string;
  body: string;
  stageLabel: string;
  updatedAt: string;
  formatting: EditorFormatting;
  corrections: MockCorrection[];
};
