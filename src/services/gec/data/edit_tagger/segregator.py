"""Edit segregation utilities."""

from dataclasses import dataclass

from src.services.gec.data.edit_tagger.common import Alignment
from src.services.gec.data.edit_tagger.punctuation import is_punctuation


@dataclass
class SegregatedEdits:
    """Container for segregated edits by type."""

    text: str
    punctuation_edits: list[Alignment]
    non_punctuation_edits: list[Alignment]


class EditSegregator:
    """Segregates edits by punctuation type."""

    def segregate(self, text: str, edits: list[Alignment]) -> SegregatedEdits:
        """Segregate edits into punctuation and non-punctuation."""
        punc_edits = [
            edit for edit in edits if self._is_punctuation_edit(text, text, edit)
        ]
        non_punc_edits = [
            edit for edit in edits if not self._is_punctuation_edit(text, text, edit)
        ]
        return SegregatedEdits(text, punc_edits, non_punc_edits)

    def _is_punctuation_edit(
        self, original_text: str, target_text: str, edit: Alignment
    ) -> bool:
        original_text_edited = original_text[edit.source_start : edit.source_end]
        target_text_edited = target_text[edit.target_start : edit.target_end]
        return is_punctuation(original_text_edited) and is_punctuation(
            target_text_edited
        )

    def build_target_no_pnx(self, edits: list[Alignment]) -> list[Alignment]:
        """Build target text without punctuation edits."""
        return [edit for edit in edits if not self._is_punctuation_edit("", "", edit)]
