import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EditableDocument } from "./EditableDocument";
import { applyEditorInput } from "./inputOperations";
import type { Correction } from "./types";

const correction: Correction = {
  id: "correction-1",
  category: "spelling",
  status: "active",
  span: { start: 3, end: 7 },
  title: "تصحيح",
  lineLabel: "السطر 1",
  original: "جميل",
  replacement: "جميلٌ",
  explanation: "شرح",
  ruleLabel: "قاعدة",
};

const formatting = {
  strong: [],
  emphasis: [],
  lines: {},
};

describe("EditableDocument", () => {
  it("renders valid correction ranges and reports correction selection", () => {
    const onCorrectionFocus = vi.fn();
    render(
      <EditableDocument
        body="نص جميل"
        corrections={[correction]}
        focusedCorrectionId={null}
        formatting={formatting}
        onBodyChange={vi.fn()}
        onCorrectionFocus={onCorrectionFocus}
        onSelectionChange={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByText("جميل"));
    expect(onCorrectionFocus).toHaveBeenCalledWith("correction-1");
  });

  it("applies consecutive text and line-break inputs without adding whitespace", () => {
    let result = applyEditorInput("سطر أول", [7, 7], "insertText", " جديد");
    result = applyEditorInput(result.body, result.selection, "insertParagraph");
    result = applyEditorInput(
      result.body,
      result.selection,
      "insertText",
      "سطر ثان",
    );

    expect(result.body).toBe("سطر أول جديد\nسطر ثان");
    expect(result.body.match(/\n/g)).toHaveLength(1);
  });

  it("replaces selections and deletes one character predictably", () => {
    const replaced = applyEditorInput("نص قديم", [3, 8], "insertText", "جديد");
    const deleted = applyEditorInput(
      replaced.body,
      replaced.selection,
      "deleteContentBackward",
    );

    expect(replaced.body).toBe("نص جديد");
    expect(deleted.body).toBe("نص جدي");
  });
});
