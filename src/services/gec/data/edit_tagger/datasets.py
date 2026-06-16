from data import dataclass

from src.services.gec.data.edit_tagger.common import Alignment
from src.services.gec.data.edit_tagger.segregator import EditSegregator


@dataclass
class ParallelExample:
    source: str
    target: str

class DatasetSegregator:
    def __init__(self):
        self.edit_segregator = EditSegregator()

    def build_examples(self, source_text: str, target_text: str, edits: list[Alignment]
                       )-> tuple[ParallelExample, ParallelExample]:
        nopnx_target = self.edit_segregator.build_target_no_pnx(source_text=source_text, edits=edits)
        pnx = ParallelExample(source_text, target_text)
        nopnx = ParallelExample(source_text, nopnx_target)
        return (pnx, nopnx)

class DatasetExporter:
    def export_jsonl():
        pass