import {
  useLayoutEffect,
  useMemo,
  useRef,
  type ClipboardEvent,
  type KeyboardEvent,
  type MouseEvent,
  type ReactNode,
} from "react";

import type {
  EditorFormatting,
  EditorTextRange,
  MockCorrection,
} from "./types";
import { applyEditorInput } from "./inputOperations";
import { getLineFormat } from "./useEditorDemo";

type EditableDocumentProps = {
  body: string;
  corrections: MockCorrection[];
  focusedCorrectionId: string | null;
  formatting: EditorFormatting;
  onBodyChange: (body: string) => void;
  onCorrectionFocus: (correctionId: string) => void;
  onSelectionChange: (range: EditorTextRange) => void;
};

function getLineStart(body: string, lineIndex: number) {
  let start = 0;
  for (let index = 0; index < lineIndex; index += 1) {
    const nextBreak = body.indexOf("\n", start);
    if (nextBreak === -1) return body.length;
    start = nextBreak + 1;
  }
  return start;
}

function getPointOffset(
  root: HTMLElement,
  body: string,
  node: Node,
  offset: number,
) {
  const line =
    node instanceof HTMLElement
      ? node.closest<HTMLElement>("[data-editor-line]")
      : node.parentElement?.closest<HTMLElement>("[data-editor-line]");
  if (!line) return body.length;

  const lineIndex = Number(line.dataset.editorLine ?? 0);
  const range = document.createRange();
  range.selectNodeContents(line);
  try {
    range.setEnd(node, offset);
  } catch {
    return getLineStart(body, lineIndex) + (line.textContent?.length ?? 0);
  }
  return getLineStart(body, lineIndex) + range.toString().length;
}

function captureSelection(
  root: HTMLElement,
  body: string,
): EditorTextRange | null {
  const selection = window.getSelection();
  if (
    !selection?.anchorNode ||
    !selection.focusNode ||
    !root.contains(selection.anchorNode) ||
    !root.contains(selection.focusNode)
  ) {
    return null;
  }

  return [
    getPointOffset(root, body, selection.anchorNode, selection.anchorOffset),
    getPointOffset(root, body, selection.focusNode, selection.focusOffset),
  ];
}

function findTextPoint(root: HTMLElement, requestedOffset: number) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let remaining = Math.max(0, requestedOffset);
  let current = walker.nextNode();
  let lastTextNode: Node | null = null;

  while (current) {
    lastTextNode = current;
    const length = current.textContent?.length ?? 0;
    if (remaining <= length) return { node: current, offset: remaining };
    remaining -= length;
    current = walker.nextNode();
  }

  return lastTextNode
    ? { node: lastTextNode, offset: lastTextNode.textContent?.length ?? 0 }
    : { node: root, offset: 0 };
}

function findPointForOffset(root: HTMLElement, body: string, offset: number) {
  const lines = body.split("\n");
  let lineStart = 0;

  for (let lineIndex = 0; lineIndex < lines.length; lineIndex += 1) {
    const lineLength = lines[lineIndex]?.length ?? 0;
    if (offset <= lineStart + lineLength || lineIndex === lines.length - 1) {
      const line = root.querySelector<HTMLElement>(
        `[data-editor-line="${lineIndex}"]`,
      );
      if (!line) return { node: root, offset: 0 };
      return findTextPoint(line, Math.max(0, offset - lineStart));
    }
    lineStart += lineLength + 1;
  }

  return { node: root, offset: 0 };
}

function restoreSelection(
  root: HTMLElement,
  body: string,
  [anchorOffset, focusOffset]: EditorTextRange,
) {
  const selection = window.getSelection();
  if (!selection) return;
  const anchor = findPointForOffset(root, body, anchorOffset);
  const focus = findPointForOffset(root, body, focusOffset);
  selection.setBaseAndExtent(
    anchor.node,
    anchor.offset,
    focus.node,
    focus.offset,
  );
}

function rangeContains(ranges: EditorTextRange[], start: number, end: number) {
  return ranges.some(([from, to]) => from <= start && to >= end);
}

function renderLineContent(
  body: string,
  line: string,
  lineStart: number,
  corrections: MockCorrection[],
  formatting: EditorFormatting,
) {
  if (line.length === 0) return <br />;
  const lineEnd = lineStart + line.length;
  const activeCorrections = corrections.filter(
    (correction) =>
      correction.status === "active" &&
      correction.span[0] < lineEnd &&
      correction.span[1] > lineStart &&
      body.slice(...correction.span) === correction.original,
  );
  const boundaries = new Set([lineStart, lineEnd]);

  for (const correction of activeCorrections) {
    boundaries.add(Math.max(lineStart, correction.span[0]));
    boundaries.add(Math.min(lineEnd, correction.span[1]));
  }
  for (const ranges of [formatting.strong, formatting.emphasis]) {
    for (const [start, end] of ranges) {
      if (start < lineEnd && end > lineStart) {
        boundaries.add(Math.max(lineStart, start));
        boundaries.add(Math.min(lineEnd, end));
      }
    }
  }

  const points = [...boundaries].sort((left, right) => left - right);
  const children: ReactNode[] = [];

  for (let index = 0; index < points.length - 1; index += 1) {
    const start = points[index] ?? lineStart;
    const end = points[index + 1] ?? lineEnd;
    const text = body.slice(start, end);
    const correction = activeCorrections.find(
      (entry) => entry.span[0] <= start && entry.span[1] >= end,
    );
    const strong = rangeContains(formatting.strong, start, end);
    const emphasis = rangeContains(formatting.emphasis, start, end);
    const content =
      strong || emphasis ? (
        <span
          className="editor-page__formatted-text"
          data-emphasis={emphasis || undefined}
          data-strong={strong || undefined}
        >
          {text}
        </span>
      ) : (
        text
      );

    children.push(
      correction ? (
        <mark
          className="editor-page__highlight"
          data-correction-id={correction.id}
          key={`${start}-${end}`}
        >
          {content}
        </mark>
      ) : (
        <span key={`${start}-${end}`}>{content}</span>
      ),
    );
  }

  return children;
}

function renderDocument(
  body: string,
  corrections: MockCorrection[],
  focusedCorrectionId: string | null,
  formatting: EditorFormatting,
) {
  let lineStart = 0;
  return body.split("\n").map((line, lineIndex) => {
    const format = getLineFormat(formatting, lineIndex);
    const content = renderLineContent(
      body,
      line,
      lineStart,
      corrections,
      formatting,
    );
    const containsFocusedCorrection = corrections.some(
      (correction) =>
        correction.id === focusedCorrectionId &&
        correction.span[0] <= lineStart + line.length &&
        correction.span[1] >= lineStart,
    );
    const currentStart = lineStart;
    lineStart += line.length + 1;

    return (
      <div
        className="editor-page__text-line"
        data-active={containsFocusedCorrection || undefined}
        data-align={format.align}
        data-editor-line={lineIndex}
        data-list={format.list}
        data-list-label={
          format.list === "numbered" ? `${lineIndex + 1}.` : undefined
        }
        key={`${lineIndex}-${currentStart}`}
      >
        {content}
      </div>
    );
  });
}

export function EditableDocument({
  body,
  corrections,
  focusedCorrectionId,
  formatting,
  onBodyChange,
  onCorrectionFocus,
  onSelectionChange,
}: EditableDocumentProps) {
  const editorRef = useRef<HTMLDivElement>(null);
  const selectionRef = useRef<EditorTextRange>([0, 0]);
  const compositionRangeRef = useRef<EditorTextRange | null>(null);
  const documentContent = useMemo(
    () => renderDocument(body, corrections, focusedCorrectionId, formatting),
    [body, corrections, focusedCorrectionId, formatting],
  );

  useLayoutEffect(() => {
    const editor = editorRef.current;
    if (!editor || document.activeElement !== editor) return;
    restoreSelection(editor, body, selectionRef.current);
  }, [body, corrections, formatting]);

  useLayoutEffect(() => {
    if (!focusedCorrectionId) return;
    editorRef.current
      ?.querySelector<HTMLElement>(
        `[data-correction-id="${focusedCorrectionId}"]`,
      )
      ?.scrollIntoView({ block: "center", behavior: "smooth" });
  }, [focusedCorrectionId]);

  const updateSelection = (target: HTMLDivElement) => {
    const range = captureSelection(target, body);
    if (!range) return;
    selectionRef.current = range;
    onSelectionChange(range);
  };

  const applyInput = (target: HTMLDivElement, inputType: string, data = "") => {
    const captured = captureSelection(target, body) ?? selectionRef.current;
    const sourceRange =
      inputType === "insertCompositionText" && compositionRangeRef.current
        ? compositionRangeRef.current
        : captured;
    const result = applyEditorInput(body, sourceRange, inputType, data);
    selectionRef.current = result.selection;
    if (inputType === "insertCompositionText") {
      compositionRangeRef.current = [sourceRange[0], result.selection[0]];
    }
    onSelectionChange(result.selection);
    onBodyChange(result.body);
  };

  const handleBeforeInput = (inputEvent: InputEvent) => {
    const target = editorRef.current;
    if (!target) return;
    const supported =
      inputEvent.inputType.startsWith("insert") ||
      inputEvent.inputType.startsWith("delete");
    if (!supported) return;
    inputEvent.preventDefault();
    applyInput(target, inputEvent.inputType, inputEvent.data ?? "");
  };

  const handlePaste = (event: ClipboardEvent<HTMLDivElement>) => {
    event.preventDefault();
    applyInput(
      event.currentTarget,
      "insertFromPaste",
      event.clipboardData.getData("text/plain"),
    );
  };

  const handleClick = (event: MouseEvent<HTMLDivElement>) => {
    const correction = (event.target as HTMLElement).closest<HTMLElement>(
      "[data-correction-id]",
    );
    const correctionId = correction?.dataset.correctionId;
    if (correctionId) onCorrectionFocus(correctionId);
    updateSelection(event.currentTarget);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape") event.currentTarget.blur();
  };

  useLayoutEffect(() => {
    const editor = editorRef.current;
    if (!editor) return;
    editor.addEventListener("beforeinput", handleBeforeInput);
    return () => editor.removeEventListener("beforeinput", handleBeforeInput);
  });

  return (
    <div
      aria-label="محتوى النص"
      aria-multiline="true"
      className="editor-page__document-text"
      contentEditable="plaintext-only"
      dir="auto"
      onClick={handleClick}
      onCompositionEnd={() => {
        compositionRangeRef.current = null;
      }}
      onCompositionStart={(event) => {
        compositionRangeRef.current =
          captureSelection(event.currentTarget, body) ?? selectionRef.current;
      }}
      onFocus={(event) => updateSelection(event.currentTarget)}
      onKeyDown={handleKeyDown}
      onKeyUp={(event) => updateSelection(event.currentTarget)}
      onMouseUp={(event) => updateSelection(event.currentTarget)}
      onPaste={handlePaste}
      ref={editorRef}
      role="textbox"
      spellCheck={false}
      suppressContentEditableWarning
    >
      {documentContent}
    </div>
  );
}
