"""Dictionary-based GEC correction module."""

from src.services.gec.modules.dictionary.engine import DictionaryEngine
from src.services.gec.schemas import (
    GECInput,
    ModuleResult,
)
from src.services.gec.serving.module import GECModule


class DictionaryService(GECModule):
    """GEC module that proposes corrections from a dictionary engine."""

    def __init__(self):
        """Initialize DictionaryService with a dictionary engine."""
        self.dictionary_engine = DictionaryEngine()

    def run(self, input: GECInput) -> ModuleResult:
        """Run the dictionary module and return candidate edits."""
        result: ModuleResult = self.dictionary_engine.process(input)
        return result
