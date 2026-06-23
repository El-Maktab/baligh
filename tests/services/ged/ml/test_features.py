"""Tests for GED ML features."""

from src.core.schemas import MorphAnalysis, Token
from src.services.ged.features.subsystems.ml.features import (
    sentence_features,
)


def _token(index: int, form: str, affix_structure: str | None = None) -> Token:
    return Token(
        index=index,
        form=form,
        span=(index, index + len(form)),
        norm_span=(index, index + len(form)),
        affix_structure=affix_structure,
    )


def _analysis(index: int, pos: str, *, lemma: str | None = None) -> MorphAnalysis:
    return MorphAnalysis(
        token_index=index,
        pos=pos,
        lemma=lemma,
        is_disambiguated=True,
    )


def test_features_include_context_boundaries_and_morphology() -> None:
    """Sentence features preserve context and preprocessing morphology."""
    rows = sentence_features(
        [
            _token(0, "ذهب", "STEM"),
            _token(1, "الطلاب", "DET+STEM"),
            _token(2, ".", None),
        ],
        [
            [_analysis(0, "VERB", lemma="ذهب")],
            [_analysis(1, "NOUN", lemma="طالب")],
            [_analysis(2, "PUNC")],
        ],
    )

    assert rows[0]["BOS"] is True
    assert rows[0]["next_token"] == "الطلاب"
    assert rows[0]["morph_pos"] == "VERB"
    assert rows[1]["prev_token"] == "ذهب"
    assert rows[1]["next_token"] == "."
    assert rows[1]["prev_morph_pos"] == "VERB"
    assert rows[1]["affix_structure"] == "DET+STEM"
    assert rows[2]["EOS"] is True
    assert rows[2]["is_punct"] is True


def test_features_apply_arabic_normalization() -> None:
    """Alif and alif maqsura normalization matches notebook training."""
    row = sentence_features(
        [_token(0, "إلى", "STEM")],
        [[_analysis(0, "PREP", lemma="إلى")]],
    )[0]

    assert row["norm"] == "الي"
    assert row["prefix_1"] == "إ"
    assert row["suffix_1"] == "ى"
