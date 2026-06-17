"""Dataset handling for edit tagging."""

from data import dataclass
from src.services.gec.data.edit_tagger.common import Alignment
from src.services.gec.data.edit_tagger.segregator import EditSegregator
from src.services.gec.utils.rewriter import Rewriter


@dataclass
class ParallelExample:
    """Parallel example with source and target text."""

    source: str
    target: str


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
        seg_edit = self.edit_segregator.segregate(source_text=source_text, edits=edits)
        pnx = self.rewriter.apply_char_edits(source_text, seg_edit.punctuation_edits)
        nopnx = self.rewriter.apply_char_edits(
            source_text, seg_edit.non_punctuation_edits
        )
        return ParallelExample(pnx, nopnx)


class DatasetExporter:
    """Exports datasets to JSONL format."""

    @staticmethod
    def export_jsonl():
        """Export dataset to JSONL format."""
        pass
