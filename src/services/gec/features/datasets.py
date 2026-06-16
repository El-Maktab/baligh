#TODO: UNUSED

"""Dataset handling for edit tagging."""
from pathlib import Path

from src.services.gec.modules.edit_tagger.common import Alignment, ParallelExample
from src.services.gec.modules.edit_tagger.segregator import EditSegregator
from src.services.gec.modules.edit_tagger.rewriter import Rewriter


class DatasetSegregator:
    """Segregates datasets based on edit types."""

    def __init__(self):
        """Initialize the dataset segregator."""
        self.edit_segregator = EditSegregator()
        self.rewriter = Rewriter()

    def build_examples(
        self, source_text: str, target_text: str, edits: list[Alignment]
    ) -> tuple[ParallelExample, ParallelExample]:
        """Build parallel examples from source, target, and edits."""
        seg_edit = self.edit_segregator.segregate(source_text, edits)
        pnx = self.rewriter.apply_char_edits(source_text, seg_edit.punctuation_edits)
        nopnx = self.rewriter.apply_char_edits(
            source_text, seg_edit.non_punctuation_edits
        )
        return (ParallelExample(source_text, pnx), ParallelExample(source_text, nopnx))
