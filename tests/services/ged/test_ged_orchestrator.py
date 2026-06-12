"""Test GED Orchestrator.

Authors:
    Amir Anwar
"""

from src.services.ged.exceptions import GEDDetectionError
from src.services.ged.features.subsystems.base import BaseDetector
from src.services.ged.orchestrator import GEDService
from src.services.ged.schemas import (
    ErrorCategory,
    ErrorSource,
    ErrorSpan,
    GEDInput,
    MorphAnalysis,
    ProvenanceTier,
    Token,
)


class MockDetector(BaseDetector):
    """A mock detector that flags the first token as an error."""

    def __init__(self, name: str = "mock_detector", throw_error: bool = False) -> None:
        """Initialize the mock detector."""
        self._name = name
        self.throw_error = throw_error

    @property
    def name(self) -> str:
        """Return the name of the detector."""
        return self._name

    def detect(
        self,
        text: str,
        normalized_text: str,
        tokens: list[Token],
        morph_features: list[list[MorphAnalysis]],
    ) -> list[ErrorSpan]:
        """Detect errors in input text."""
        if self.throw_error:
            raise GEDDetectionError(
                message="Mock failure",
                detector_name=self.name,
            )

        if not tokens:
            return []

        # Return a dummy error for the first token
        first_token = tokens[0]
        return [
            ErrorSpan(
                span=first_token.span,
                token_refs=[first_token.index],
                category=ErrorCategory.ORTHOGRAPHY,
                subtype="mock_error",
                confidence=0.9,
                sources=[ErrorSource.RULE_BASED],
                provenance_tier=ProvenanceTier.TIER_1_RULE_DERIVED,
                explanation_eligible=True,
                explanation_text=f"Mock explanation for {first_token.form}",
            )
        ]


def test_orchestrator_graceful_failure():
    """Verify orchestrator continues executing if one subsystem fails."""
    failing_detector = MockDetector("broken_detector", throw_error=True)
    working_detector = MockDetector("working_detector")
    service = GEDService(subsystems=[failing_detector, working_detector])

    payload = GEDInput(
        text="ذهب الطلاب",
        normalized_text="ذهب الطلاب",
        tokens=[
            Token(index=0, form="ذهب", span=(0, 3), norm_span=(0, 3), is_clitic=False),
        ],
        morph_features=[[]],
    )

    output = service.process(payload)

    # Even though broken_detector raised GEDDetectionError
    # working_detector runs successfully
    assert len(output.errors) == 1
    assert output.errors[0].sources == [ErrorSource.RULE_BASED]
