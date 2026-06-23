"""Tests for the machine-learned GED detector."""

from sklearn_crfsuite import CRF
from src.core.schemas import MorphAnalysis, Token
from src.services.ged.features.subsystems.ml.detector import MLDetector
from src.services.ged.schemas import ErrorCategory, ErrorSource, ProvenanceTier


class FakeCRF(CRF):
    """Return fixed marginals for detector tests."""

    classes_ = ["UC", "OT", "MG", "SP", "UNK"]

    def __init__(self, marginals: list[dict[str, float]]) -> None:
        """Store fixed token marginals."""
        self.marginals = marginals

    def predict_marginals(
        self, features: list[list[dict[str, object]]]
    ) -> list[list[dict[str, float]]]:
        """Return the fixed marginals as one sentence."""
        return [self.marginals]


def _token(index: int, form: str, span: tuple[int, int]) -> Token:
    return Token(index=index, form=form, span=span, norm_span=span)


def _detector(marginals: list[dict[str, float]]) -> MLDetector:
    manifest = {
        "features": {"version": "surface_morph_v2"},
        "inference": {"error_threshold": 0.35},
    }
    return MLDetector(model=FakeCRF(marginals), manifest=manifest)


def _analysis(index: int, pos: str) -> list[MorphAnalysis]:
    return [MorphAnalysis(token_index=index, pos=pos, is_disambiguated=True)]


def test_detector_thresholds_predictions_and_uses_real_offsets() -> None:
    """Accepted predictions use preprocessing indices and offsets."""
    tokens = [_token(4, "هاذا", (3, 7)), _token(5, "كتاب", (8, 12))]
    detector = _detector(
        [
            {"UC": 0.2, "OT": 0.8},
            {"UC": 0.7, "SP": 0.3},
        ]
    )

    spans = detector.detect(
        "", "", tokens, [_analysis(0, "NOUN"), _analysis(1, "NOUN")]
    )

    assert len(spans) == 1
    assert spans[0].span == (3, 7)
    assert spans[0].token_refs == [4]
    assert spans[0].category == ErrorCategory.ORTHOGRAPHY
    assert spans[0].confidence == 0.8
    assert spans[0].sources == [ErrorSource.SEQUENCE_LABELER]
    assert spans[0].provenance_tier == ProvenanceTier.TIER_3_STATISTICAL
    assert spans[0].explanation_eligible is False


def test_detector_groups_merges_but_keeps_splits_separate() -> None:
    """Merge runs form one span while split labels remain token-local."""
    tokens = [
        _token(0, "في", (0, 2)),
        _token(1, "ما", (3, 5)),
        _token(2, "كلما", (6, 10)),
        _token(3, "حينما", (11, 16)),
    ]
    detector = _detector(
        [
            {"MG": 0.9},
            {"MG": 0.7},
            {"SP": 0.8},
            {"SP": 0.6},
        ]
    )

    spans = detector.detect(
        "",
        "",
        tokens,
        [
            _analysis(0, "PREP"),
            _analysis(1, "PART"),
            _analysis(2, "NOUN"),
            _analysis(3, "NOUN"),
        ],
    )

    assert [(span.span, span.token_refs, span.category) for span in spans] == [
        ((0, 5), [0, 1], ErrorCategory.MERGE),
        ((6, 10), [2], ErrorCategory.SPLIT),
        ((11, 16), [3], ErrorCategory.SPLIT),
    ]
    assert spans[0].confidence == 0.7


def test_detector_suppresses_unknown_predictions() -> None:
    """Report-only UNK predictions do not leak into the public schema."""
    detector = _detector([{"UNK": 0.9}])

    assert (
        detector.detect("", "", [_token(0, "شيء", (0, 3))], [_analysis(0, "NOUN")])
        == []
    )
