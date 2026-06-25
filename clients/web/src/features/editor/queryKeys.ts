export const editorQueryKeys = {
  drafts: ["editor", "drafts"] as const,
  draft: (draftId: string) => ["editor", "draft", draftId] as const,
  analysis: (draftId: string) => ["editor", "analysis", draftId] as const,
  suggestions: (draftId: string) => ["editor", "suggestions", draftId] as const,
};
