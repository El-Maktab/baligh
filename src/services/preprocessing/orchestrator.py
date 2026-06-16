"""Orchestrator for the Baligh preprocessing pipeline.

This module runse the full preprocessing pipeline:

    1. Normalization        (normalize_with_mapping)
    2. Word Boundary        (split_word_boundary)
    3. Segmentation         (segment)
    4. Morphological Analy  (analyze)

References:
- docs/contracts/preprocessing-contract.md

Authors:
    - Akram Hany
"""

from src.services.preprocessing.features.analyzer import analyze
from src.services.preprocessing.features.segmenter import segment
from src.services.preprocessing.schemas import PreprocessingInput, PreprocessingOutput
from src.services.preprocessing.utils.boundary import split_word_boundary
from src.services.preprocessing.utils.normalizer import normalize_with_mapping


def preprocess(input: PreprocessingInput) -> PreprocessingOutput:
    """Runs the full preprocessing pipeline on raw user input.

    runs the four stages in order:
        1. Normalization -> Unicode NFKC + whitespace consolidation.
        2. Word Boundary Detection -> splits completed prefix from the current 
            fragment being typed and determines NWP vs WAC mode.
        3. Segmentation -> Farasa segments completed tokens, calculating
            affix_structure and character offsets.
        4. Morphological Analysis -> CAMeL Tools produces per-token
            MorphAnalysis candidates with the disambiguated candidate first.

    Args:
        input: A PreprocessingInput containing the raw Arabic text and an
            optional cursor_offset (currently unsupported, must be None).

    Returns:
        A PreprocessingOutput containing the original text, normalized text,
        completed tokens, per-token morphological candidates, the current
        fragment (or None), and the detected mode.
    """
    # 1. Normalization                                             
    normalized_text, norm_to_orig_map = normalize_with_mapping(input.text)

    # 2. Word Boundary Detection                                   
    completed_prefix, current_fragment, mode = split_word_boundary(
        normalized_text, input.cursor_offset
    )

    # 3. Segmentation (completed prefix only)                     
    tokens = segment(completed_prefix, norm_to_orig_map)

    # 4. Morphological Analysis + Disambiguation                  
    morph_features = analyze(tokens)

    return PreprocessingOutput(
        text=input.text,
        normalized_text=normalized_text,
        tokens=tokens,
        morph_features=morph_features,
        current_fragment=current_fragment,
        mode=mode,
    )
