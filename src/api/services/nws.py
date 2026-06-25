"""Thin wrapper around the NWS (Next Word Suggestion) pipeline.

It receives a ``PreprocessingOutput`` and constructs the required ``NWSInput``
model, then calls the cache manager to retrieve suggestions.
If the actual NWS model is unavailable, this stub returns an empty list.
"""

from typing import Literal

from src.services.nws.schemas import NWSInput, NWSOutput


def run(preproc_output, mode: Literal["NWP", "WAC"], top_k: int = 5) -> NWSOutput:
    """Run NWS suggestion lookup.

    ``preproc_output`` is a ``PreprocessingOutput`` instance.
    ``mode`` and ``top_k`` are forwarded to the cache manager.
    When the real model is missing, an empty ``NWSOutput`` is returned.
    """
    try:
        _nws_input = NWSInput(
            tokens=preproc_output.tokens,
            morph_features=preproc_output.morph_features,
            current_fragment=preproc_output.current_fragment,
            mode=mode,
            top_k=top_k,
        )
        # manager = CacheManager()
        # suggestions = manager.lookup_or_compute(nws_input)
        return NWSOutput(mode=mode, suggestions=[])
    except Exception:
        return NWSOutput(mode=mode, suggestions=[])
