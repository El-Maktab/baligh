import { describe, expect, it } from "vitest";

import {
  applyTashkeel,
  createInitialEditorState,
  editorDemoReducer,
  getActiveDraft,
  getCorrectionCounts,
} from "./useEditorDemo";

describe("editorDemoReducer", () => {
  it("adds a local draft and selects it immediately", () => {
    const state = createInitialEditorState();
    const nextState = editorDemoReducer(state, { type: "addDraft" });

    expect(nextState.activeDraftId).toBe("draft-3");
    expect(nextState.drafts[0]?.title).toBe("نص جديد 3");
    expect(nextState.drafts[0]?.stageLabel).toBe("محلي فقط");
  });

  it("accepts a correction by replacing the original text and removing it from counts", () => {
    const state = createInitialEditorState();
    const nextState = editorDemoReducer(state, {
      type: "acceptCorrection",
      correctionId: "correction-3",
    });

    const draft = getActiveDraft(nextState);
    expect(draft.body).toContain("يعتني");
    expect(draft.body).not.toContain("يعتن بالتفاصيل");
    expect(getCorrectionCounts(draft).all).toBe(3);
  });

  it("marks unmatched active corrections as stale after direct text edits", () => {
    const state = createInitialEditorState();
    const nextState = editorDemoReducer(state, {
      type: "updateBody",
      body: "نص جديد بدون أي مواضع تصحيح أصلية.",
    });

    const draft = getActiveDraft(nextState);
    expect(
      draft.corrections.filter((correction) => correction.status === "stale"),
    ).toHaveLength(4);
  });

  it("shifts later correction ranges when text is inserted before them", () => {
    const state = createInitialEditorState();
    const draft = getActiveDraft(state);
    const nextState = editorDemoReducer(state, {
      type: "updateBody",
      body: `مقدمة ${draft.body}`,
    });

    const shifted = getActiveDraft(nextState).corrections.find(
      (correction) => correction.id === "correction-3",
    );
    expect(shifted?.span).toEqual({ start: 258, end: 262 });
    expect(shifted?.status).toBe("active");
  });

  it("marks only a correction overlapping a manual edit as stale", () => {
    const state = createInitialEditorState();
    const draft = getActiveDraft(state);
    const nextBody = draft.body.slice(0, 13) + "وترفّق" + draft.body.slice(18);
    const nextState = editorDemoReducer(state, {
      type: "updateBody",
      body: nextBody,
    });

    const corrections = getActiveDraft(nextState).corrections;
    expect(corrections[0]?.status).toBe("stale");
    expect(
      corrections.slice(1).every(({ status }) => status === "active"),
    ).toBe(true);
  });

  it("applies inline formatting only to the selected range", () => {
    const state = createInitialEditorState();
    const formatted = editorDemoReducer(state, {
      type: "toggleStrong",
      range: [0, 7],
    });
    const switched = editorDemoReducer(formatted, {
      type: "selectDraft",
      draftId: "draft-2",
    });

    expect(formatted.drafts[0]?.formatting.strong).toEqual([[0, 7]]);
    expect(getActiveDraft(switched).formatting.strong).toEqual([]);
  });

  it("formats the current line when the selection is collapsed", () => {
    const state = createInitialEditorState();
    const formatted = editorDemoReducer(state, {
      type: "toggleEmphasis",
      range: [5, 5],
    });

    expect(getActiveDraft(formatted).formatting.emphasis).toEqual([[0, 19]]);
  });

  it("adds tashkeel to the selected text range", () => {
    const state = createInitialEditorState();
    const formatted = editorDemoReducer(state, {
      type: "applyTashkeel",
      range: [0, 18],
    });

    expect(
      getActiveDraft(formatted).body.startsWith("المَحَبَّة تَتَأَنَّى"),
    ).toBe(true);
  });

  it("adds tashkeel to the current line when the selection is collapsed", () => {
    const state = createInitialEditorState();
    const formatted = editorDemoReducer(state, {
      type: "applyTashkeel",
      range: [253, 253],
    });

    expect(getActiveDraft(formatted).body).toContain("يَعتَنِ");
    expect(getActiveDraft(formatted).body).toContain("بِالتَّفَاصِيل");
  });

  it("applies block formatting only to lines intersecting the selection", () => {
    const state = createInitialEditorState();
    const formatted = editorDemoReducer(state, {
      type: "cycleList",
      range: [20, 20],
    });

    expect(getActiveDraft(formatted).formatting.lines[1]?.list).toBe("bullet");
    expect(getActiveDraft(formatted).formatting.lines[0]).toBeUndefined();
  });

  it("leaves unmatched text unchanged when no tashkeel mapping exists", () => {
    expect(applyTashkeel("hello world", [0, 5])).toEqual({
      body: "hello world",
      applied: false,
    });
  });
});
