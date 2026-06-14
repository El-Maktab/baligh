"""Ontology-based GEC correction module."""

from src.services.gec.modules.ontology.engine import OntologyEngine
from src.services.gec.schemas import (
    GECInput,
    ModuleResult,
)
from src.services.gec.serving.module import GECModule


class OntologyService(GECModule):
    """GEC module that proposes corrections from an ontology engine."""

    def __init__(self):
        """Initialize OntologyService with an ontology engine."""
        self.ontology_engine = OntologyEngine()

    def run(self, input: GECInput) -> ModuleResult:
        """Run the ontology module and return candidate edits."""
        res: ModuleResult = self.ontology_engine.process(input)
        return res
