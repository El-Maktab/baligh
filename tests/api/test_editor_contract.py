"""Tests for editor-facing correction normalization."""

from src.api.services.editor_contract import (
    normalize_candidate_edit,
    normalize_error_detection,
)
from src.services.gec.schemas import ModuleName
from src.services.ged.schemas import (
    ErrorCategory,
    ErrorSource,
    ErrorSpan,
    ProvenanceTier,
)
from src.services.ranker.schemas import RankedEdit


def test_normalize_candidate_prefers_ged_fallback_for_split() -> None:
    """Tier-3 split spans should still use a GED explanation ahead of GEC text."""
    candidate = RankedEdit(
        error_id=0,
        span=(0, 4),
        token_refs=[0],
        correction="يا رب",
        selected_module=ModuleName.DICTIONARY,
        final_score=0.8,
        edit_confidence=0.9,
        explanation="اقتراح من القاموس",
        alternatives=["يا رب"],
    )
    error_span = ErrorSpan(
        span=(0, 4),
        token_refs=[0],
        category=ErrorCategory.SPLIT,
        subtype="ml_split",
        confidence=0.9,
        sources=[ErrorSource.SEQUENCE_LABELER],
        provenance_tier=ProvenanceTier.TIER_3_STATISTICAL,
        explanation_eligible=False,
        explanation_text=None,
    )

    normalized = normalize_candidate_edit(
        correction_id="corr-1",
        body="يارب",
        candidate=candidate,
        module_name=ModuleName.DICTIONARY,
        error_span=error_span,
    )

    assert normalized["explanation"] == "رصد المدقق أن هذا الموضع يحتاج إلى فصل."
    assert normalized["ruleLabel"] == "SP / ml_split"


def test_normalize_detection_prefers_ged_fallback_for_split() -> None:
    """Pure GED detections should also expose the GED split fallback text."""
    error_span = ErrorSpan(
        span=(0, 4),
        token_refs=[0],
        category=ErrorCategory.SPLIT,
        subtype="ml_split",
        confidence=0.9,
        sources=[ErrorSource.SEQUENCE_LABELER],
        provenance_tier=ProvenanceTier.TIER_3_STATISTICAL,
        explanation_eligible=False,
        explanation_text=None,
    )

    normalized = normalize_error_detection(
        detection_id="det-1",
        body="يارب",
        error_span=error_span,
    )

    assert normalized["explanation"] == "رصد المدقق أن هذا الموضع يحتاج إلى فصل."
    assert normalized["ruleLabel"] == "SP / ml_split"
