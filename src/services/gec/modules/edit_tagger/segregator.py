"""Edit segregation utilities."""

from dataclasses import dataclass

from src.services.gec.modules.edit_tagger.common import Alignment
from src.services.gec.modules.edit_tagger.common import ProjectedExample
from src.services.gec.modules.edit_tagger.punctuation import is_punctuation, PUNCTUATION_SET


@dataclass
class SegregatedEdits:
    """Container for segregated edits by type."""

    text: str
    punctuation_edits: list[Alignment]
    non_punctuation_edits: list[Alignment]

class SimpleSegregatedEdits:
    punctuation_edits: list[str]
    non_punctuation_edits: list[str]

class EditSegregator:
    """Segregates edits by punctuation type."""
    def simple_segregate(self, edits: list[ProjectedExample]) -> SimpleSegregatedEdits :
        punc_edits = []
        no_punc_edits = []
        for edit in edits:
            for label in edit.labels:
                contains_punct = any(punct in label for punct in PUNCTUATION_SET)
                if(contains_punct): punc_edits.append(label)
                else: no_punc_edits.append(label)
        return SimpleSegregatedEdits(punc_edits, no_punc_edits)

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
