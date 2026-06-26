"""Router for the analysis endpoint.

Runs the full preprocessing → GED → GEC pipeline for a given draft.
"""

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from src.api.services.drafts import get_draft, update_draft
from src.api.services.gec import run as gec_run
from src.api.services.ged import run as ged_run
from src.api.services.preprocessing import run as preprocess_run
from src.services.gec.schemas import CandidateEdit, ModuleName

router = APIRouter()


class AnalysisCorrection(BaseModel):
    """Model for representing a correction in the analysis response."""

    id: str
    span: dict[str, int]
    token_refs: list[int]
    correction: str
    alternatives: list[str] | None = None
    explanation: str | None = None
    edit_confidence: float | None = None
    category: str
    status: str = "active"


class AnalyzeRequest(BaseModel):
    """Request model for the analyze endpoint."""

    title: str | None = None
    body: str | None = None
    selection: dict[str, int] | None = None
    caret: int | None = None
    clientRevision: int | None = None
    categories: list[str] | None = None


class AnalyzeResponse(BaseModel):
    """Response model for the analyze endpoint."""

    analysisRevision: int
    corrections: list[AnalysisCorrection] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)


@router.post("/{draft_id}/analyze", response_model=AnalyzeResponse)
async def analyze_draft(draft_id: str, payload: AnalyzeRequest):
    """Analyze a draft, persist corrections, and return results."""
    draft = await get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if payload.body:
        body = payload.body
    else:
        body = draft.body if draft.body else ""
    preproc = preprocess_run(body)
    _ = ged_run(preproc)
    gec_output = gec_run(preproc)

    total = 0
    spelling = 0
    grammar = 0
    style = 0
    response_corrections: list[CandidateEdit] = []
    persist_corrections: list[dict] = []

    for module_result in gec_output:
        count = len(module_result.candidate_edits)
        total += count
        response_corrections.extend(module_result.candidate_edits)

        if module_result.module_name == ModuleName.DICTIONARY:
            spelling += count
            category = "spelling"
        elif module_result.module_name == ModuleName.ONTOLOGY:
            grammar += count
            category = "grammar"
        else:
            style += count
            category = "style"

        for edit in module_result.candidate_edits:
            persist_corrections.append(
                {
                    "id": f"corr-{uuid.uuid4()}",
                    "span": {"start": edit.span[0], "end": edit.span[1]},
                    "token_refs": edit.token_refs,
                    "correction": edit.correction,
                    "alternatives": getattr(edit, "alternatives", []),
                    "explanation": edit.explanation,
                    "edit_confidence": getattr(edit, "edit_confidence", None),
                    "category": category,
                    "status": "active",
                }
            )

    counts = {
        "all": total,
        "spelling": spelling,
        "grammar": grammar,
        "style": style,
    }

    updated = await update_draft(draft_id, body=body, corrections=persist_corrections)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update draft")

    return AnalyzeResponse(
        analysisRevision=updated.revision,
        corrections=[AnalysisCorrection(**corr) for corr in persist_corrections],
        counts=counts,
    )
