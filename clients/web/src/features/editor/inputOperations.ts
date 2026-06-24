import type { EditorTextRange } from "./types";

type TextInputResult = {
  body: string;
  selection: EditorTextRange;
};

function normalizeSelection(
  body: string,
  [anchor, focus]: EditorTextRange,
): EditorTextRange {
  return [
    Math.max(0, Math.min(anchor, focus, body.length)),
    Math.max(0, Math.min(Math.max(anchor, focus), body.length)),
  ];
}

function previousCharacterStart(body: string, offset: number) {
  const character = Array.from(body.slice(0, offset)).at(-1);
  return Math.max(0, offset - (character?.length ?? 1));
}

function nextCharacterEnd(body: string, offset: number) {
  const character = Array.from(body.slice(offset))[0];
  return Math.min(body.length, offset + (character?.length ?? 1));
}

export function applyEditorInput(
  body: string,
  selection: EditorTextRange,
  inputType: string,
  data = "",
): TextInputResult {
  let [start, end] = normalizeSelection(body, selection);
  let insertion = data;

  if (inputType === "insertParagraph" || inputType === "insertLineBreak") {
    insertion = "\n";
  } else if (inputType.startsWith("delete")) {
    insertion = "";
    if (start === end && inputType.includes("Backward")) {
      start = previousCharacterStart(body, start);
    } else if (start === end) {
      end = nextCharacterEnd(body, end);
    }
  }

  const nextBody = body.slice(0, start) + insertion + body.slice(end);
  const caret = start + insertion.length;
  return { body: nextBody, selection: [caret, caret] };
}
