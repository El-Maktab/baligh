"""Text rewriting utilities for error correction."""

from src.services.gec.data.edit_tagger.common import Alignment
from src.services.gec.schemas import EditOperation


class Rewriter:
    def apply_edits(text: str, edits: list[Alignment]) -> str:
        """Apply the character level edits to the text."""

        result = []
        cursor = 0

        for edit in edits:
            if edit.operation == EditOperation.KEEP:
                result.append(text[cursor])
                cursor = edit.source_start + 1

            elif edit.operation == EditOperation.REPLACE:
                result.append(edit.label)
                cursor = edit.source_start + 1

            elif edit.operation == EditOperation.DELETE:
                cursor = edit.source_start + 1

            elif edit.operation == EditOperation.INSERT:
                result.append(edit.label)
                cursor = edit.source_start

            else:
                raise ValueError(
                    f"Unsupported operation: {edit.operation}"
                )

        return "".join(result)