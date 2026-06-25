"""Thin wrapper around the preprocessing orchestrator.

It validates the input via the Pydantic schema and returns the
`PreprocessingOutput` model defined in the services package.
"""

from src.services.preprocessing.orchestrator import preprocess
from src.services.preprocessing.schemas import PreprocessingInput, PreprocessingOutput


def run(text: str) -> PreprocessingOutput:
    """Run preprocessing on raw ``text``.

    The wrapper creates a ``PreprocessingInput`` (cursor_offset is unused) and
    forwards it to the orchestrator.
    """
    inp = PreprocessingInput(text=text, cursor_offset=None)
    return preprocess(inp)
