#TODO: UNUSED
from dataclasses import dataclass

from src.services.gec.modules.edit_tagger.common import ParallelExample


@dataclass
class M2Edit:
    start: int
    end: int
    error_type: str
    correction: str
    annotator_id: int


class M2Parser:
    """Parses M2 files into ParallelExample objects."""

    def _parse_edit(self, line: str) -> M2Edit:
        line = line[2:]

        parts = line.split("|||")

        span = parts[0]
        error_type = parts[1]
        correction = parts[2]
        annotator = int(parts[-1])

        start, end = map(int, span.split())

        return M2Edit(
            start=start,
            end=end,
            error_type=error_type,
            correction=correction,
            annotator_id=annotator,
        )

    def _apply_edits(self, tokens: list[str], edits: list[M2Edit]) -> str:
        tokens = tokens.copy()
        for edit in sorted(edits, key=lambda e: e.start, reverse=True):
            replacement = [] if edit.correction == "-NONE-" else edit.correction.split()

            tokens[edit.start : edit.end] = replacement

        return " ".join(tokens)
