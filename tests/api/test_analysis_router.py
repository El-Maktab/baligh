"""Tests for the analysis router with partial GEC/GED outputs."""

from __future__ import annotations

import asyncio

from src.api.routers.analysis import analyze_draft
from src.api.routers.suggestions import get_suggestions
from src.api.services.drafts import DraftDocument
from src.api.services.editor_contract import AnalyzeRequest, SuggestionRequest
from src.services.gec.schemas import ModuleName
from src.services.ged.schemas import (
    ErrorCategory,
    ErrorSource,
    ErrorSpan,
    GEDOutput,
    ProvenanceTier,
)
from src.services.ranker.schemas import RankedEdit, RankerOutput, RankingMetadata


def test_analysis_allows_partial_gec_results(monkeypatch) -> None:
    """Analysis should normalize a subset of enabled modules without placeholders."""
    error_span = ErrorSpan(
        span=(5, 8),
        token_refs=[1],
        category=ErrorCategory.ORTHOGRAPHY,
        subtype="hamza",
        confidence=0.9,
        sources=[ErrorSource.LEXICON_MATCHER],
        provenance_tier=ProvenanceTier.TIER_1_RULE_DERIVED,
        explanation_eligible=True,
        explanation_text="حرف الجر إلى يُكتب بهمزة قطع",
    )

    async def _get_draft(_draft_id: str) -> DraftDocument:
        return DraftDocument(
            id="draft-1",
            title="Draft",
            body="ذهب الى",
            stageLabel="جاهز",
            updatedAt="الآن",
            savedAt="2026-01-01T00:00:00+00:00",
            revision=1,
            formatting={},
            corrections=[],
        )

    async def _update_draft(*args, **kwargs) -> DraftDocument:  # noqa: ANN002, ANN003
        return DraftDocument(
            id="draft-1",
            title="Draft",
            body="ذهب الى",
            stageLabel="جاهز",
            updatedAt="الآن",
            savedAt="2026-01-01T00:00:00+00:00",
            revision=2,
            formatting={},
            corrections=kwargs["corrections"],
        )

    def _corrections_run(_body: str):
        return (
            RankerOutput(
                text="ذهب الى",
                ranked_edits=[
                    RankedEdit(
                        error_id=0,
                        span=(5, 8),
                        token_refs=[1],
                        correction="إلى",
                        selected_module=ModuleName.DICTIONARY,
                        final_score=0.9,
                        edit_confidence=0.9,
                        alternatives=["إلى"],
                    )
                ],
                ranking_metadata=RankingMetadata(
                    global_confidence=0.9,
                    module_utilization={"DICTIONARY": 1},
                ),
            ),
            GEDOutput(text="ذهب الى", errors=[error_span]),
        )

    monkeypatch.setattr("src.api.routers.analysis.get_draft", _get_draft)
    monkeypatch.setattr("src.api.routers.analysis.update_draft", _update_draft)
    monkeypatch.setattr("src.api.routers.analysis.corrections_run", _corrections_run)

    response = asyncio.run(analyze_draft("draft-1", AnalyzeRequest(body="ذهب الى")))

    assert response.analysisRevision == 2
    assert len(response.corrections) == 1
    assert response.corrections[0].sourceModule == ModuleName.DICTIONARY.value
    assert response.counts["spelling"] == 1


def test_suggestions_fall_back_when_nws_is_disabled(monkeypatch) -> None:
    """Suggestions should still work via fallback when NWS returns no results."""

    async def _get_draft(_draft_id: str) -> DraftDocument:
        return DraftDocument(
            id="draft-1",
            title="Draft",
            body="الم",
            stageLabel="جاهز",
            updatedAt="الآن",
            savedAt="2026-01-01T00:00:00+00:00",
            revision=1,
            formatting={},
            corrections=[],
        )

    class _DisabledNWSOutput:
        suggestions = []

    monkeypatch.setattr("src.api.routers.suggestions.get_draft", _get_draft)
    monkeypatch.setattr(
        "src.api.routers.suggestions.nws_run",
        lambda _body: _DisabledNWSOutput(),
    )

    response = asyncio.run(
        get_suggestions(
            "draft-1",
            SuggestionRequest(
                body="الم",
                selection={"start": 0, "end": 3},
                caret=3,
                mode="word",
            ),
        )
    )

    assert response.suggestions
    assert response.suggestions[0].kind == "word"
