"""Router for the analysis endpoint.

Runs the full preprocessing → GED → GEC pipeline for a given draft.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from src.api.services.drafts import get_draft, update_draft
from src.api.services.gec import run as gec_run
from src.api.services.ged import run as ged_run
from src.api.services.preprocessing import run as preprocess_run
from src.services.gec.schemas import CandidateEdit

router = APIRouter()


class AnalyzeRequest(BaseModel):
    """Request model for the analyze endpoint."""

    body: str
    selection: str | None = None
    caret: int | None = None
    clientRevision: int | None = None
    categories: list[str] | None = None


class AnalyzeResponse(BaseModel):
    """Response model for the analyze endpoint."""

    analysisRevision: int
    corrections: list[CandidateEdit]
    counts: dict[str, int] = Field(default_factory=dict)


@router.post("/{draft_id}/analyze", response_model=AnalyzeResponse)
async def analyze_draft(draft_id: str, payload: AnalyzeRequest):
    """Analyze a draft and return correction suggestions."""
    draft = await get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    preproc = preprocess_run(payload.body)
    _ = ged_run(preproc)
    gec_output = gec_run(preproc)
    updated = await update_draft(draft_id, body=payload.body)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update draft")

    total = 0
    corrections = []
    for module_output in gec_output:
        total += len(module_output.candidate_edits)
        corrections.extend([c for c in module_output.candidate_edits])

    return AnalyzeResponse(
        analysisRevision=updated.revision,
        corrections=corrections,
        counts={"total": total},
    )
