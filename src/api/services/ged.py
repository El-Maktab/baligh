"""Thin wrapper around the GED orchestrator.

It constructs the required ``GEDInput`` model and invokes ``GEDService``.
"""

from src.services.ged.orchestrator import GEDService
from src.services.ged.schemas import GEDInput, GEDOutput

# Assuming a default GEDService instance with desired detectors is available.
# For simplicity we instantiate it with an empty list (no detectors) –
# in a real deployment you would pass concrete detector instances here.


def run(preproc_output) -> GEDOutput:
    """Run the GED stage.

    ``preproc_output`` is expected to be a ``PreprocessingOutput`` instance.
    The function builds a ``GEDInput`` and calls the service.
    """
    payload = GEDInput(
        text=preproc_output.text,
        normalized_text=preproc_output.normalized_text,
        tokens=preproc_output.tokens,
        morph_features=preproc_output.morph_features,
    )
    service = GEDService(subsystems=[])
    return service.process(payload)
