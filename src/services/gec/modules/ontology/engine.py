"""Main Ontology Engine orchestrator."""

from loguru import logger

from src.services.gec.modules.dictionary.arramooz_client import ArramoozClient
from src.services.gec.modules.dictionary.morph_generator import MorphologicalGenerator
from src.services.gec.schemas import (
    GECInput,
    ModuleName,
    ModuleResult,
    ModuleStatus,
)

from .candidate_generator import CandidateGenerator
from .explanation_generator import ExplanationGenerator
from .loader import OntologyLoader


class OntologyEngine:
    """Orchestrates loading, querying, and generating grammar corrections."""

    def __init__(self, arramooz_client: ArramoozClient | None = None) -> None:
        """Initializes the OntologyEngine."""
        self._loader = OntologyLoader()
        self._loader.load_graph()  # Load the OWL graph into memory

        self._arramooz_client = arramooz_client or ArramoozClient()
        self._morph_generator = MorphologicalGenerator(self._arramooz_client)
        self._explanation_generator = ExplanationGenerator()

        self._candidate_generator = CandidateGenerator(
            self._loader,
            self._morph_generator,
            self._explanation_generator,
        )
        logger.info("OntologyEngine initialized successfully")

    def process(self, input_data: GECInput) -> ModuleResult:
        """Process GECInput to identify grammatical errors and return corrections.

        Args:
            input_data: Request structure with tokens, morph features, and error spans.

        Returns:
            ModuleResult containing grammatical correction edits.
        """
        logger.info(
            "tokens={} errors_span={}",
            len(input_data.tokens),
            len(input_data.errors_span),
        )
        try:
            edits = self._candidate_generator.generate_candidates(
                input_data.text,
                input_data.tokens,
                input_data.errors_span,
                input_data.morph_features,
            )
            status = ModuleStatus.INCORRECT if edits else ModuleStatus.CORRECT
            logger.info(
                "OntologyEngine processing complete | edits={} status={}",
                len(edits),
                status,
            )
            return ModuleResult(
                module_name=ModuleName.ONTOLOGY,
                status=status,
                candidate_edits=edits,
            )
        except Exception:
            logger.exception("Error during OntologyEngine processing")
            return ModuleResult(
                module_name=ModuleName.ONTOLOGY,
                status=ModuleStatus.ERROR,
                candidate_edits=[],
            )
