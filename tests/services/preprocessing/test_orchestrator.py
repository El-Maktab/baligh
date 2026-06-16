"""Integration tests for the preprocessing orchestrator.

These tests require all CAMeL Tools and Farasa models to be installed.
"""

from src.services.preprocessing import (
    PreprocessingInput,
    PreprocessingOutput,
    preprocess,
)

#############################################################################
# Helpers
#############################################################################


def _run(text: str) -> PreprocessingOutput:
    """Convenience wrapper around preprocess()."""
    return preprocess(PreprocessingInput(text=text))


#############################################################################
# Empty / whitespace-only input
#############################################################################


def test_preprocess_empty_string():
    """Empty input should return a valid, empty PreprocessingOutput in NWP mode."""
    out = _run("")
    assert out.text == ""
    assert out.normalized_text == ""
    assert out.tokens == []
    assert out.morph_features == []
    assert out.current_fragment is None
    assert out.mode == "NWP"


def test_preprocess_whitespace_only():
    """Whitespace-only input ends with a delimiter -> NWP, no tokens."""
    out = _run("   ")
    assert out.mode == "NWP"
    assert out.current_fragment is None
    assert out.tokens == []
    assert out.morph_features == []


#############################################################################
# Mode detection
#############################################################################


def test_preprocess_nwp_mode_delimiter_ending():
    """Input ending with a delimiter -> NWP mode, current_fragment is None."""
    out = _run("ذهب الطلاب ")
    assert out.mode == "NWP"
    assert out.current_fragment is None


def test_preprocess_wac_mode_incomplete_word():
    """Input NOT ending with a delimiter -> WAC mode, current_fragment is set."""
    out = _run("ذهب الطلاب إلى المدرس")
    assert out.mode == "WAC"
    assert out.current_fragment is not None
    assert out.current_fragment != ""


#############################################################################
# Different shapes for input
#############################################################################


def test_preprocess_morph_features_length_matches_tokens():
    """morph_features outer list must have the same length as tokens."""
    out = _run("ذهب الطلاب، إلى المدرسة ")
    assert len(out.morph_features) == len(out.tokens)


def test_preprocess_each_token_has_at_least_one_analysis():
    """Every token must have at least one MorphAnalysis candidate."""
    out = _run("ذهب الطلاب، إلى المدرسة ")
    for i, candidates in enumerate(out.morph_features):
        assert len(candidates) >= 1, f"Token {i} has no analyses"


def test_preprocess_disambiguated_is_first():
    """Index 0 of every token's candidate list must be is_disambiguated=True."""
    out = _run("ذهب الطلاب إلى المدرسة ")
    for i, candidates in enumerate(out.morph_features):
        assert candidates[0].is_disambiguated is True, (
            f"Token {i}: first candidate is not the disambiguated one"
        )


#############################################################################
# Data integrity
#############################################################################


def test_preprocess_original_text_preserved():
    """output.text must equal the original raw input exactly."""
    raw = "ذهب  الطلابُ  إلى  المدرسة"
    out = _run(raw)
    assert out.text == raw


def test_preprocess_token_indices_are_sequential():
    """Token.index values must be 0, 1, 2, ... in order."""
    out = _run("ذهب الطلاب إلى المدرسة ")
    for expected_idx, token in enumerate(out.tokens):
        assert token.index == expected_idx


def test_preprocess_token_index_matches_morph_analysis():
    """MorphAnalysis.token_index must match the token's own index."""
    out = _run("ذهب الطلاب إلى المدرسة ")
    for token, candidates in zip(out.tokens, out.morph_features, strict=False):
        for c in candidates:
            assert c.token_index == token.index


def test_preprocess_wac_fragment_not_in_tokens():
    """The current_fragment (incomplete word) must not appear as a token."""
    out = _run("ذهب إلى المدرس")
    assert out.mode == "WAC"
    fragment = out.current_fragment
    token_forms = [t.form for t in out.tokens]
    assert fragment not in token_forms
