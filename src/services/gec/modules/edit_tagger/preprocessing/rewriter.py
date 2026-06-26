"""Text rewriting utilities for error correction."""

import re

from src.services.gec.modules.edit_tagger.common import Alignment
from src.services.gec.schemas import EditOperation

_TAG_RE = re.compile(r"^([KDIRMS])(?:_\[([^\]]*)\])?(\d+|\*)?$")


def _parse_tag(tag: str) -> tuple[str, str | None]:
    m = _TAG_RE.match(tag)
    if m is None:
        return "K", None
    op = m.group(1)
    label = m.group(2)
    return op, label


class Rewriter:
    """Applies character-level edits to text."""

    def apply_word_edits(self, text: str, edits: list[Alignment]) -> list[str]:
        """Apply the word level edits to the text."""
        result = []
        cursor = 0
        text_list = text.split(" ")
        for edit in edits:
            if edit.operation == EditOperation.KEEP:
                result.append(text_list[cursor])

            elif edit.operation == EditOperation.REPLACE:
                if edit.label is not None:
                    result.append(text_list[cursor])
                else:
                    result.append(text_list[cursor])

            elif edit.operation == EditOperation.INSERT:
                result.append(" ")

            elif edit.operation == EditOperation.DELETE:
                pass

            elif edit.operation == EditOperation.MERGE:
                result.append(
                    "".join(text_list[edit.source_start : edit.source_end + 1])
                )

            elif edit.operation == EditOperation.SPLIT:
                result.append(text_list[edit.source_start])

            else:
                raise ValueError(f"Unsupported operation: {edit.operation}")
            cursor = edit.source_end + 1
        return result

    def apply_char_edits(self, text: str, edits: list[Alignment]) -> str:
        """Apply the character level edits to the text."""
        result = []
        cursor = 0

        for edit in edits:
            if edit.operation == EditOperation.KEEP:
                result.append(text[cursor])
                cursor = edit.source_start + 1

            elif edit.operation == EditOperation.REPLACE:
                if edit.label is not None:
                    result.append(edit.label)
                cursor = edit.source_start + 1

            elif edit.operation == EditOperation.DELETE:
                cursor = edit.source_start + 1

            elif edit.operation == EditOperation.INSERT:
                if edit.label is not None:
                    result.append(edit.label)
                cursor = edit.source_start

            else:
                raise ValueError(f"Unsupported operation: {edit.operation}")

        return "".join(result)

    def apply_tag(self, token: list[str], tag: list[str]) -> str:
        """Apply a sequence of edit tags to a list of tokens."""
        TAG_SEQ_RE = re.compile(r"([KDIRMS])(?:_\[([^\]]*)\])?(\d+|\*)?")
        words = []
        current_word_parts: list[str] = []

        for t, t_tag in zip(token, tag):
            if t.startswith("##"):
                is_subword = True
                clean_t = t[2:]
            else:
                is_subword = False
                clean_t = t

            if not is_subword and current_word_parts:
                words.append("".join(current_word_parts))
                current_word_parts = []

            ops = []
            for m in TAG_SEQ_RE.finditer(t_tag):
                ops.append((m.group(1), m.group(2), m.group(3)))

            explicit_len = 0
            for op, label, quant in ops:
                if op != "I":
                    if quant is None:
                        explicit_len += 1
                    elif quant != "*":
                        explicit_len += int(quant)

            star_len = max(0, len(clean_t) - explicit_len)

            res = []
            cursor = 0
            for op, label, quant in ops:
                if op == "I":
                    if label is not None:
                        res.append(label)
                else:
                    if quant == "*":
                        step = star_len
                        star_len = 0
                    elif quant is None:
                        step = 1
                    else:
                        step = int(quant)

                    actual_step = min(step, max(0, len(clean_t) - cursor))
                    sub = clean_t[cursor : cursor + actual_step]
                    cursor += actual_step

                    if op == "K":
                        res.append(sub)
                    elif op == "R":
                        if label is not None:
                            res.append(label)

            current_word_parts.append("".join(res))

        if current_word_parts:
            words.append("".join(current_word_parts))

        return " ".join([w for w in words if w])
