"""Edit-tagger GEC correction module."""

from pathlib import Path

from transformers import AutoModelForTokenClassification

from src.services.gec.modules.edit_tagger.engine import TaggerEngine
from src.services.gec.schemas import (
    GECInput,
    ModuleResult,
)
from src.services.gec.serving.module import GECModule
from src.services.gec.utils.string_utils import Tokenizer


class EditTaggerService(GECModule):
    """GEC module that proposes corrections from a trained edit-tagger model."""

    def __init__(self):
        """Initialize EditTaggerService."""
        best_model_path = Path("src/services/gec/models/edit_tagger_v1/checkpoint-3642")
        inference_model = AutoModelForTokenClassification.from_pretrained(
            best_model_path
        )
        tokenizer = Tokenizer()
        self.tagger_engine = TaggerEngine(model=inference_model, tokenizer=tokenizer)

    def run(self, input: GECInput) -> ModuleResult:
        """Run the tagger module and return candidate edits."""
        return self.tagger_engine.process(payload=input)
