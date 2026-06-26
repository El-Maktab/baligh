"""Thin wrapper around the NWS (Next Word Suggestion) pipeline."""

from src.api.services.baligh_singleton import get_baligh
from src.services.nws.schemas import NWSOutput
from src.services.preprocessing.schemas import PreprocessingOutput


def run(input_text: str) -> NWSOutput:
    """Run NWS suggestion lookup."""
    return get_baligh().run_nws(input_text)
