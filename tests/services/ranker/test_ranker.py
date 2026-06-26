"""Regression tests for ranker span-to-candidate alignment."""

from src.core.schemas import Token
from src.services.gec.schemas import (
    CandidateEdit,
    ModuleName,
    ModuleResult,
    ModuleStatus,
)
from src.services.ged.schemas import (
    ErrorCategory,
    ErrorSource,
    ErrorSpan,
    ProvenanceTier,
)
from src.services.ranker.ranker import RankerService
from src.services.ranker.schemas import RankerInput


def _token(index: int, form: str, span: tuple[int, int]) -> Token:
    return Token(index=index, form=form, span=span, norm_span=span)


def _error(span: tuple[int, int], token_ref: int, subtype: str) -> ErrorSpan:
    return ErrorSpan(
        span=span,
        token_refs=[token_ref],
        category=ErrorCategory.ORTHOGRAPHY,
        subtype=subtype,
        confidence=0.9,
        sources=[ErrorSource.RULE_BASED],
        provenance_tier=ProvenanceTier.TIER_1_RULE_DERIVED,
        explanation_eligible=True,
        explanation_text="test",
    )


def _module_result(candidate: CandidateEdit) -> ModuleResult:
    return ModuleResult(
        module_name=ModuleName.DICTIONARY,
        status=ModuleStatus.INCORRECT,
        candidate_edits=[candidate],
    )


def test_rank_keeps_candidate_on_its_original_error_span() -> None:
    """A candidate for the first GED error must not drift to the next one."""
    text = "اكتب الى"
    tokens = [_token(0, "اكتب", (0, 4)), _token(1, "الى", (5, 8))]
    errors = [_error((0, 4), 0, "ml_orthography"), _error((5, 8), 1, "hamza")]
    candidate = CandidateEdit(
        span=(0, 4),
        token_refs=[0],
        correction="مكتب",
        edit_confidence=0.95,
        alternatives=["مكتب"],
    )

    output = RankerService().rank(
        RankerInput(
            text=text,
            tokens=tokens,
            errors_span=errors,
            errors_corrections=[_module_result(candidate)],
        )
    )

    assert len(output.ranked_edits) == 1
    assert output.ranked_edits[0].error_id == 0
    assert output.ranked_edits[0].span == (0, 4)
    assert output.ranked_edits[0].correction == "مكتب"


def test_rank_preserves_candidates_for_the_last_error() -> None:
    """A candidate matched to the final GED error should not be dropped."""
    text = "اكتب الى"
    tokens = [_token(0, "اكتب", (0, 4)), _token(1, "الى", (5, 8))]
    errors = [_error((0, 4), 0, "ml_orthography"), _error((5, 8), 1, "hamza")]
    candidate = CandidateEdit(
        span=(5, 8),
        token_refs=[1],
        correction="إلى",
        edit_confidence=0.95,
        alternatives=["إلى"],
    )

    output = RankerService().rank(
        RankerInput(
            text=text,
            tokens=tokens,
            errors_span=errors,
            errors_corrections=[_module_result(candidate)],
        )
    )

    assert len(output.ranked_edits) == 1
    assert output.ranked_edits[0].error_id == 1
    assert output.ranked_edits[0].span == (5, 8)
    assert output.ranked_edits[0].correction == "إلى"


def test_rank_prefers_ged_explanation_over_gec_explanation() -> None:
    """GED explanation text should win when both GED and GEC provide one."""
    text = "كبيرة"
    tokens = [_token(0, "كبيرة", (0, 5))]
    errors = [
        ErrorSpan(
            span=(0, 5),
            token_refs=[0],
            category=ErrorCategory.SYNTAX,
            subtype="noun_adjective_agreement",
            confidence=0.9,
            sources=[ErrorSource.RULE_BASED],
            provenance_tier=ProvenanceTier.TIER_1_RULE_DERIVED,
            explanation_eligible=True,
            explanation_text="تفسير GED",
        )
    ]
    candidate = CandidateEdit(
        span=(0, 5),
        token_refs=[0],
        correction="كبير",
        edit_confidence=0.95,
        explanation="تفسير GEC",
        alternatives=["كبير"],
    )

    output = RankerService().rank(
        RankerInput(
            text=text,
            tokens=tokens,
            errors_span=errors,
            errors_corrections=[
                ModuleResult(
                    module_name=ModuleName.ONTOLOGY,
                    status=ModuleStatus.INCORRECT,
                    candidate_edits=[candidate],
                )
            ],
        )
    )

    assert len(output.ranked_edits) == 1
    assert output.ranked_edits[0].correction == "كبير"
    assert output.ranked_edits[0].explanation == "تفسير GED"
