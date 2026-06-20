"""Tests for the NWS service schemas.

Authors:
    - Akram Hany
"""

import pytest
from pydantic import ValidationError
from src.core.schemas import MorphAnalysis, Token
from src.services.nws.schemas import NWSInput, NWSOutput, NWSSource, Suggestion


def test_nws_source_values():
    """Verify that NWSSource enum values match the contract."""
    assert NWSSource.IDIOM_CACHE == "idiom_cache"
    assert NWSSource.PHRASE_CACHE == "phrase_cache"
    assert NWSSource.USER_CACHE == "user_cache"
    assert NWSSource.MODEL == "model"
    assert NWSSource.TRIE == "trie"


def test_suggestion_validation():
    """Verify that Suggestion model validates correctly."""
    # Valid suggestion
    s = Suggestion(rank=0, word="ذهب", score=0.9, source=NWSSource.MODEL)
    assert s.rank == 0
    assert s.word == "ذهب"
    assert s.score == 0.9
    assert s.source == "model"

    # Invalid source
    with pytest.raises(ValidationError):
        Suggestion(rank=0, word="ذهب", score=0.9, source="invalid_source")


def test_nws_input_defaults():
    """Verify default values for NWSInput fields."""
    tokens = [Token(index=0, form="ذهب", span=(0, 3), norm_span=(0, 3))]
    morph_features = [[MorphAnalysis(token_index=0, pos="VERB")]]

    nws_input = NWSInput(
        tokens=tokens,
        morph_features=morph_features,
        mode="NWP",
    )
    assert nws_input.tokens == tokens
    assert nws_input.morph_features == morph_features
    assert nws_input.mode == "NWP"
    assert nws_input.current_fragment is None
    assert nws_input.top_k == 5


def test_nws_input_validation():
    """Verify that NWSInput model validates correctly with custom and invalid opts."""
    tokens = [Token(index=0, form="ذهب", span=(0, 3), norm_span=(0, 3))]
    morph_features = [[MorphAnalysis(token_index=0, pos="VERB")]]

    # Valid WAC input
    nws_input = NWSInput(
        tokens=tokens,
        morph_features=morph_features,
        current_fragment="المدرس",
        mode="WAC",
        top_k=3,
    )
    assert nws_input.current_fragment == "المدرس"
    assert nws_input.mode == "WAC"
    assert nws_input.top_k == 3

    # Invalid mode
    with pytest.raises(ValidationError):
        NWSInput(
            tokens=tokens,
            morph_features=morph_features,
            mode="INVALID_MODE",
        )


def test_nws_output_validation():
    """Verify that NWSOutput model validates correctly."""
    suggestions = [
        Suggestion(rank=0, word="المدرسة", score=0.9, source=NWSSource.TRIE),
        Suggestion(rank=1, word="المدرسين", score=0.7, source=NWSSource.TRIE),
    ]

    # Valid output
    output = NWSOutput(mode="WAC", suggestions=suggestions)
    assert output.mode == "WAC"
    assert output.suggestions == suggestions

    # Invalid mode
    with pytest.raises(ValidationError):
        NWSOutput(mode="INVALID_MODE", suggestions=suggestions)
