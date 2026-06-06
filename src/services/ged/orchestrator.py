"""GED Orchestrator.

Passes GED input to all subsystems and resolves conflicts between them.

Authors:
  Amir Anwar
"""

from src.services.ged.exceptions import GEDDetectionError
from src.services.ged.features.subsystems.base import BaseDetector
from src.services.ged.fusion import resolve_overlaps
from src.services.ged.schemas import ErrorSpan, GEDInput, GEDOutput


class GEDService:
    """GED Orchestrator.

    This class is responsible for orchestrating the GED process. It takes the input,
        passes it to all subsystems, collects their outputs,
        and then resolves any conflicts between them using the fusion layer.
    """

    def __init__(self, subsystems: list[BaseDetector]):
        """Initialize GED with a list of subsystems."""
        self.subsystems = subsystems

    def process(self, payload: GEDInput) -> GEDOutput:
        """Process GED input and return errors.

        Args:
            payload: GEDInput containing the text and its features.

        Returns:
            GEDOutput containing the original text and the list of detected errors.
        """
        errors: list[ErrorSpan] = []

        for detector in self.subsystems:
            try:
                detector_errors = detector.detect(
                    payload.text,
                    payload.normalized_text,
                    payload.tokens,
                    payload.morph_features,
                )
                errors.extend(detector_errors)
            except GEDDetectionError as e:
                # NOTE: needs proper logging and error handling
                print(f"[GED] {e.detector_name} error: {str(e)}")

        fused_errors = resolve_overlaps(errors)

        return GEDOutput(text=payload.text, errors=fused_errors)
