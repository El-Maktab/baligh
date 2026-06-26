"""Tests for preprocessing-backed tashkeel helpers."""

from src.api.services.editor_contract import EditorSelection
from src.api.services.tashkeel import (
    apply_tashkeel_with_preprocessing,
    resolve_tashkeel_range,
)
from src.core.schemas import MorphAnalysis, Token
from src.services.preprocessing.schemas import PreprocessingOutput


def test_resolve_tashkeel_range_expands_collapsed_selection_to_line():
    """A collapsed selection should diacritize the current line."""
    body = "السطر الأول\nالسطر الثاني\nالسطر الثالث"

    result = resolve_tashkeel_range(body, EditorSelection(start=14, end=14))

    assert result == EditorSelection(start=12, end=24)


def test_apply_tashkeel_with_preprocessing_uses_diacritized_tokens():
    """Token diacritics from preprocessing should replace the original surface."""
    text = "ذهب الطالب"
    preprocessing_output = PreprocessingOutput(
        text=text,
        normalized_text=text,
        tokens=[
            Token(index=0, form="ذهب", span=(0, 3)),
            Token(index=1, form="الطالب", span=(4, 10)),
        ],
        morph_features=[
            [MorphAnalysis(token_index=0, pos="VERB", diacritized="ذَهَبَ")],
            [MorphAnalysis(token_index=1, pos="NOUN", diacritized="الطَّالِبُ")],
        ],
        current_fragment=None,
        mode="NWP",
    )

    assert apply_tashkeel_with_preprocessing(text, preprocessing_output) == "ذَهَبَ الطَّالِبُ"
