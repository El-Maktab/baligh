"""Text rewriting utilities for error correction."""

from src.services.gec.modules.edit_tagger.common import Alignment
from src.services.gec.schemas import EditOperation


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

    import re


    def apply_tag(token: list[str], tag: list[str]) -> str:
        pass