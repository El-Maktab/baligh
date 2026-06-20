"""Tests for GED ML surface features."""

from src.services.ged.features.subsystems.ml.features import (
    sentence_surface_v1_features,
)


def test_surface_features_include_context_and_boundaries() -> None:
    """Sentence features preserve the training schema and local context."""
    rows = sentence_surface_v1_features(["ذهب", "الطلاب", "."])

    assert rows[0]["BOS"] is True
    assert rows[0]["next_token"] == "الطلاب"
    assert rows[1]["prev_token"] == "ذهب"
    assert rows[1]["next_token"] == "."
    assert rows[2]["EOS"] is True
    assert rows[2]["is_punct"] is True


def test_surface_features_apply_arabic_normalization() -> None:
    """Alif and alif maqsura normalization matches notebook training."""
    row = sentence_surface_v1_features(["إلى"])[0]

    assert row["norm"] == "الي"
    assert row["prefix_1"] == "إ"
    assert row["suffix_1"] == "ى"
