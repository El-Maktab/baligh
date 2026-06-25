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
                result.append("".join(text_list[edit.source_start:edit.source_end + 1]))

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
        words: list[str] = []
        current_word: list[str] = []
        prev_op: str | None = None

        for tok, t in zip(token, tag):
            op, label = _parse_tag(t)
            is_continuation = tok.startswith("##")
            cleaned = tok[2:] if is_continuation else tok

            if op == "K":
                if not is_continuation and current_word:
                    words.append("".join(current_word))
                    current_word = []
                current_word.append(cleaned)
            elif op == "D":
                pass
            elif op == "R":
                if not is_continuation and current_word:
                    words.append("".join(current_word))
                    current_word = []
                if label is not None:
                    current_word.append(label)
            elif op == "I":
                if not is_continuation and current_word:
                    words.append("".join(current_word))
                    current_word = []
                if label is not None:
                    words.append(label)
            elif op == "M":
                current_word.append(cleaned)
            elif op == "S":
                if current_word:
                    words.append("".join(current_word))
                    current_word = []
                current_word.append(cleaned)
            else:
                raise ValueError(f"Unsupported operation: {op}")

            prev_op = op

        if current_word:
            words.append("".join(current_word))

        return " ".join(words)
