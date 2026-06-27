"""Router for accepting or ignoring a correction."""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from src.api.services.drafts import (
    CorrectionNotAvailableError,
    RevisionConflictError,
    apply_correction,
    get_draft,
    ignore_correction,
)
from src.api.services.editor_contract import (
    AcceptCorrectionResponse,
    CorrectionActionRequest,
    IgnoreCorrectionResponse,
    RevisionConflictPayload,
    get_correction_counts,
)

router = APIRouter()


def conflict_response(
    error: RevisionConflictError | CorrectionNotAvailableError,
) -> JSONResponse:
    """Build a 409 payload the frontend can hydrate directly."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=RevisionConflictPayload(latestDraft=error.latest_draft).model_dump(
            mode="json"
        ),
    )


@router.post(
    "/{draft_id}/corrections/{correction_id}/accept",
    response_model=AcceptCorrectionResponse,
)
async def accept_correction(
    draft_id: str, correction_id: str, payload: CorrectionActionRequest
):
    """Accept a correction for a given draft."""
    draft = await get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    try:
        updated = await apply_correction(
            draft_id,
            correction_id,
            client_revision=payload.clientRevision,
            body=payload.body,
        )
    except (RevisionConflictError, CorrectionNotAvailableError) as error:
        return conflict_response(error)

    if not updated or not updated.body:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Correction not found or update failed",
        )
    return AcceptCorrectionResponse(
        draftBody=updated.body,
        persistedRevision=updated.revision,
        corrections=updated.corrections,
        counts=get_correction_counts(updated.corrections),
    )


@router.post(
    "/{draft_id}/corrections/{correction_id}/ignore",
    response_model=IgnoreCorrectionResponse,
)
async def ignore_correction_endpoint(
    draft_id: str, correction_id: str, payload: CorrectionActionRequest
):
    """Ignore a correction for a given draft."""
    draft = await get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    try:
        updated = await ignore_correction(
            draft_id,
            correction_id,
            client_revision=payload.clientRevision,
        )
    except (RevisionConflictError, CorrectionNotAvailableError) as error:
        return conflict_response(error)

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Correction not found or update failed",
        )
    return IgnoreCorrectionResponse(
        correctionId=correction_id,
        status="ignored",
        corrections=updated.corrections,
        counts=get_correction_counts(updated.corrections),
    )
