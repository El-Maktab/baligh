from data import dataclass

from src.services.gec.data.edit_tagger.common import Alignment
from src.services.gec.data.edit_tagger.punctuation import is_punctuation
from src.services.gec.utils.rewriter import Rewriter

@dataclass
class SegregatedEdits:
    punctuation_edits: list[Alignment]
    non_punctuation_edits: list[Alignment]

class EditSegregator:
    def __init__(self, rewriter: Rewriter):
        self.rewriter = rewriter

    def segregate(self, edits: list[Alignment]) -> SegregatedEdits:
        pass

    def _is_punctuation_edit(original_text: str, target_text: str, edit: Alignment) -> bool:
        original_text_edited = original_text[Alignment.source_start:Alignment.source_end]
        target_text_edited = original_text[Alignment.target_start:Alignment.target_end]
        return is_punctuation(original_text_edited) and is_punctuation(target_text_edited)


    def build_target_no_pnx(self, source_text: str, edits: list[Alignment]) -> str:
        non_punctuation_edits = [edit for edit in edits 
                                 if not self._is_punctuation_edit(edit)]
        return self.rewriter.apply_edits(source_text, non_punctuation_edits)
    
    