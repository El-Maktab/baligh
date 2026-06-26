from types import SimpleNamespace

import pytest
from src.api.routers.analysis import analyze_draft
from src.api.services.editor_contract import AnalyzeRequest
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
    GEDOutput,
    ProvenanceTier,
)


def _error(
    body: str,
    text: str,
    *,
    category: ErrorCategory,
    subtype: str,
    sources: list[ErrorSource],
) -> ErrorSpan:
    start = body.index(text)
    return ErrorSpan(
        span=(start, start + len(text)),
        token_refs=[0],
        category=category,
        subtype=subtype,
        confidence=0.87,
        sources=sources,
        provenance_tier=ProvenanceTier.TIER_1_RULE_DERIVED,
        explanation_eligible=True,
        explanation_text=f"راجع {text}",
    )


def _module_result(body: str, original: str, replacement: str) -> ModuleResult:
    start = body.index(original)
    return ModuleResult(
        module_name=ModuleName.DICTIONARY,
        status=ModuleStatus.INCORRECT,
        candidate_edits=[
            CandidateEdit(
                span=(start, start + len(original)),
                token_refs=[0],
                correction=replacement,
                edit_confidence=0.93,
                explanation="اقتراح تصحيح",
            )
        ],
    )


@pytest.mark.asyncio
async def test_analyze_draft_returns_correction_findings(monkeypatch):
    body = "هذا النص يحتوى على خطأ."
    draft = SimpleNamespace(id="draft-1", body=body)
    gec_output = [_module_result(body, "يحتوى", "يحتوي")]

    async def fake_get_draft(_draft_id):
        return draft

    async def fake_update_draft(_draft_id, **kwargs):
        return SimpleNamespace(revision=4, corrections=kwargs["corrections"])

    monkeypatch.setattr("src.api.routers.analysis.get_draft", fake_get_draft)
    monkeypatch.setattr("src.api.routers.analysis.update_draft", fake_update_draft)
    monkeypatch.setattr(
        "src.api.routers.analysis.preprocess_run",
        lambda value: SimpleNamespace(
            text=value, normalized_text=value, tokens=[], morph_features=[]
        ),
    )
    monkeypatch.setattr(
        "src.api.routers.analysis.ged_run",
        lambda _preprocessed: GEDOutput(text=body, errors=[]),
    )
    monkeypatch.setattr(
        "src.api.routers.analysis.gec_run", lambda *_args, **_kwargs: gec_output
    )

    response = await analyze_draft("draft-1", AnalyzeRequest(body=body))

    assert len(response.corrections) == 1
    finding = response.corrections[0]
    assert finding.kind == "correction"
    assert finding.actionable is True
    assert finding.replacement == "يحتوي"


@pytest.mark.asyncio
async def test_analyze_draft_returns_detection_only_findings_when_gec_is_empty(
    monkeypatch,
):
    body = "هذه جملة تنتفخ سريعاً."
    draft = SimpleNamespace(id="draft-1", body=body)
    ged_output = GEDOutput(
        text=body,
        errors=[
            _error(
                body,
                "تنتفخ",
                category=ErrorCategory.SYNTAX,
                subtype="review_only",
                sources=[ErrorSource.RULE_BASED],
            )
        ],
    )

    async def fake_get_draft(_draft_id):
        return draft

    async def fake_update_draft(_draft_id, **kwargs):
        return SimpleNamespace(revision=5, corrections=kwargs["corrections"])

    monkeypatch.setattr("src.api.routers.analysis.get_draft", fake_get_draft)
    monkeypatch.setattr("src.api.routers.analysis.update_draft", fake_update_draft)
    monkeypatch.setattr(
        "src.api.routers.analysis.preprocess_run",
        lambda value: SimpleNamespace(
            text=value, normalized_text=value, tokens=[], morph_features=[]
        ),
    )
    monkeypatch.setattr(
        "src.api.routers.analysis.ged_run", lambda _preprocessed: ged_output
    )
    monkeypatch.setattr(
        "src.api.routers.analysis.gec_run", lambda *_args, **_kwargs: []
    )

    response = await analyze_draft("draft-1", AnalyzeRequest(body=body))

    assert len(response.corrections) == 1
    finding = response.corrections[0]
    assert finding.kind == "detection"
    assert finding.actionable is False
    assert finding.replacement is None
    assert response.counts["grammar"] == 1


@pytest.mark.asyncio
async def test_analyze_draft_returns_mixed_findings_without_duplicating_matched_ged_errors(
    monkeypatch,
):
    body = "هذا النص يحتوى وتنتفخ فيه مشكلة."
    draft = SimpleNamespace(id="draft-1", body=body)
    matched = _error(
        body,
        "يحتوى",
        category=ErrorCategory.ORTHOGRAPHY,
        subtype="hamza",
        sources=[ErrorSource.LEXICON_MATCHER],
    )
    unmatched = _error(
        body,
        "تنتفخ",
        category=ErrorCategory.SYNTAX,
        subtype="review_only",
        sources=[ErrorSource.RULE_BASED],
    )

    async def fake_get_draft(_draft_id):
        return draft

    async def fake_update_draft(_draft_id, **kwargs):
        return SimpleNamespace(revision=6, corrections=kwargs["corrections"])

    monkeypatch.setattr("src.api.routers.analysis.get_draft", fake_get_draft)
    monkeypatch.setattr("src.api.routers.analysis.update_draft", fake_update_draft)
    monkeypatch.setattr(
        "src.api.routers.analysis.preprocess_run",
        lambda value: SimpleNamespace(
            text=value, normalized_text=value, tokens=[], morph_features=[]
        ),
    )
    monkeypatch.setattr(
        "src.api.routers.analysis.ged_run",
        lambda _preprocessed: GEDOutput(text=body, errors=[matched, unmatched]),
    )
    monkeypatch.setattr(
        "src.api.routers.analysis.gec_run",
        lambda *_args, **_kwargs: [_module_result(body, "يحتوى", "يحتوي")],
    )

    response = await analyze_draft("draft-1", AnalyzeRequest(body=body))

    assert len(response.corrections) == 2
    assert [finding.kind for finding in response.corrections] == [
        "correction",
        "detection",
    ]
    assert response.counts["all"] == 2
