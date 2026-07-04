"""Edit-tagger GEC correction module."""

from transformers import AutoModelForTokenClassification

from src.runtime_config import GECEditTaggerConfig, load_runtime_config
from src.services.gec.modules.edit_tagger.engine import TaggerEngine
from src.services.gec.schemas import (
    GECInput,
    ModuleResult,
)
from src.services.gec.serving.module import GECModule
from src.services.gec.utils.string_utils import Tokenizer


class EditTaggerService(GECModule):
    """GEC module that proposes corrections from a trained edit-tagger model."""

    def __init__(self, config: GECEditTaggerConfig | None = None):
        """Initialize EditTaggerService."""
        config = config or load_runtime_config().gec.edit_tagger
        inference_model = AutoModelForTokenClassification.from_pretrained(
            config.resolved_model_dir
        )
        tokenizer = Tokenizer()
        self.tagger_engine = TaggerEngine(model=inference_model, tokenizer=tokenizer)

    def run(self, input: GECInput) -> ModuleResult:
        """Run the tagger module and return candidate edits."""
        return self.tagger_engine.process(payload=input)
