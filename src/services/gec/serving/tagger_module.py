"""Edit-tagger GEC correction module."""

from src.services.gec.modules.edit_tagger.engine import TaggerEngine
from src.services.gec.schemas import (
    GECInput,
    ModuleResult,
)
from src.services.gec.serving.module import GECModule


class EditTaggerService(GECModule):
    """GEC module that proposes corrections from a trained edit-tagger model."""

    def __init__(self):
        """Initialize EditTaggerService."""
        self.tagger_engine = TaggerEngine()

    def run(self, input_txt: GECInput) -> ModuleResult:
        """Run the tagger module and return candidate edits."""
        return self.tagger_engine.process(input_txt=input_txt)
