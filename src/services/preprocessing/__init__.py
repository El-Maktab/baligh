"""Preprocessing service module for Baligh.

Public API:

    from src.services.preprocessing import preprocess, PreprocessingInput,
    PreprocessingOutput

    result = preprocess(PreprocessingInput(text="ذهب الطلاب إلى المدرسة"))
"""

from src.services.preprocessing.orchestrator import preprocess
from src.services.preprocessing.schemas import PreprocessingInput, PreprocessingOutput

__all__ = ["preprocess", "PreprocessingInput", "PreprocessingOutput"]
