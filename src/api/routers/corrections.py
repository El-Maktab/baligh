"""Router for accepting or ignoring a correction.

It updates the draft body and correction status via the repository.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from src.api.services.draft_repo import apply_correction, get_draft, ignore_correction

router = APIRouter()


class AcceptCorrectionRequest(BaseModel):
    """Request model for accepting a correction."""

    body: str | None = None
    clientRevision: int | None = None


class AcceptCorrectionResponse(BaseModel):
    """Response model for accepting a correction."""

    draftBody: str
    persistedRevision: int
    corrections: list = Field(default_factory=list)
    counts: dict = Field(default_factory=dict)


class IgnoreCorrectionRequest(BaseModel):
    """Request model for ignoring a correction."""

    body: str | None = None
    clientRevision: int | None = None


class IgnoreCorrectionResponse(BaseModel):
    """Response model for ignoring a correction."""

    correctionId: str
    status: str = "ignored"
    corrections: list = Field(default_factory=list)
    counts: dict = Field(default_factory=dict)


@router.post(
    "/{draft_id}/corrections/{correction_id}/accept",
    response_model=AcceptCorrectionResponse,
)
async def accept_correction(
    draft_id: str, correction_id: str, payload: AcceptCorrectionRequest
):
    """Accept a correction for a given draft."""
    draft = await get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    body = payload.body if payload.body is not None else draft.body
    if not body:
        raise HTTPException(status_code=400, detail="Invalid draft body")

    updated = await apply_correction(draft_id, correction_id, replacement=body)
    if not updated or not updated.body:
        raise HTTPException(
            status_code=404, detail="Correction not found or update failed"
        )
    return AcceptCorrectionResponse(
        draftBody=updated.body,
        persistedRevision=updated.revision,
        corrections=updated.corrections,
        counts={},
    )


@router.post(
    "/{draft_id}/corrections/{correction_id}/ignore",
    response_model=IgnoreCorrectionResponse,
)
async def ignore_correction_endpoint(
    draft_id: str, correction_id: str, payload: IgnoreCorrectionRequest
):
    """Ignore a correction for a given draft."""
    draft = await get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    updated = await ignore_correction(draft_id, correction_id)
    if not updated:
        raise HTTPException(
            status_code=404, detail="Correction not found or update failed"
        )
    return IgnoreCorrectionResponse(
        correctionId=correction_id,
        status="ignored",
        corrections=updated.corrections,
        counts={},
    )
