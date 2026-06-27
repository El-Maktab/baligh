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


def test_rank_keeps_unmatched_ontology_candidate_with_synthetic_span() -> None:
    """Ontology edits should survive even when GED provides no matching span."""
    text = "الولد جميل"
    tokens = [_token(0, "الولد", (0, 5)), _token(1, "جميل", (6, 10))]
    candidate = CandidateEdit(
        span=(0, 10),
        token_refs=[0, 1],
        correction="الولد جميلاً",
        edit_confidence=0.8,
        explanation="خبر إن يجب أن يكون منصوباً",
    )

    output = RankerService().rank(
        RankerInput(
            text=text,
            tokens=tokens,
            errors_span=[],
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
    assert output.ranked_edits[0].error_id == 0
    assert output.ranked_edits[0].span == (0, 10)
    assert output.ranked_edits[0].token_refs == [0, 1]
    assert output.ranked_edits[0].correction == "الولد جميلاً"
    assert output.ranked_edits[0].explanation == "خبر إن يجب أن يكون منصوباً"


def test_rank_keeps_overlapping_dictionary_and_ontology_edits() -> None:
    """Overlapping edits from different modules should both remain visible."""
    text = "الولد جميل"
    tokens = [_token(0, "الولد", (0, 5)), _token(1, "جميل", (6, 10))]
    errors = [_error((6, 10), 1, "noun_adjective_agreement")]

    dictionary_candidate = CandidateEdit(
        span=(6, 10),
        token_refs=[1],
        correction="جميلٌ",
        edit_confidence=0.85,
        alternatives=["جميلٌ"],
    )
    ontology_candidate = CandidateEdit(
        span=(6, 10),
        token_refs=[1],
        correction="جميلاً",
        edit_confidence=0.9,
        explanation="خبر إن يجب أن يكون منصوباً",
    )

    output = RankerService().rank(
        RankerInput(
            text=text,
            tokens=tokens,
            errors_span=errors,
            errors_corrections=[
                ModuleResult(
                    module_name=ModuleName.DICTIONARY,
                    status=ModuleStatus.INCORRECT,
                    candidate_edits=[dictionary_candidate],
                ),
                ModuleResult(
                    module_name=ModuleName.ONTOLOGY,
                    status=ModuleStatus.INCORRECT,
                    candidate_edits=[ontology_candidate],
                ),
            ],
        )
    )

    assert len(output.ranked_edits) == 2
    assert {edit.selected_module for edit in output.ranked_edits} == {
        ModuleName.DICTIONARY,
        ModuleName.ONTOLOGY,
    }
    assert {edit.correction for edit in output.ranked_edits} == {"جميلٌ", "جميلاً"}


def test_rank_preserves_candidate_span_when_ged_span_is_narrower() -> None:
    """Final ranked edits should keep the candidate span, not the GED span."""
    text = "قرأ الطالبين الكتابان"
    tokens = [
        _token(0, "قرأ", (0, 3)),
        _token(1, "الطالبين", (4, 12)),
        _token(2, "الكتابان", (13, 21)),
    ]
    errors = [_error((4, 12), 1, "subject_case_agreement")]
    candidate = CandidateEdit(
        span=(4, 21),
        token_refs=[1, 2],
        correction="الطالبان الكتابين",
        edit_confidence=0.9,
        explanation="الفاعل يجب أن يكون مرفوعاً ولكن وجد مجروراً",
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
    assert output.ranked_edits[0].span == (4, 21)
    assert output.ranked_edits[0].correction == "الطالبان الكتابين"
