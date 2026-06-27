"""Router for Arabic diacritization (tashkeel)."""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from src.api.services.drafts import RevisionConflictError, get_draft, update_draft
from src.api.services.editor_contract import (
    RevisionConflictPayload,
    TashkeelRequest,
    TashkeelResponse,
)
from src.api.services.tashkeel import apply_tashkeel_to_body

router = APIRouter()


def conflict_response(error: RevisionConflictError) -> JSONResponse:
    """Build a 409 payload the frontend can hydrate directly."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=RevisionConflictPayload(latestDraft=error.latest_draft).model_dump(
            mode="json"
        ),
    )


@router.post("/{draft_id}/tashkeel", response_model=TashkeelResponse)
async def apply_tashkeel(draft_id: str, payload: TashkeelRequest):
    """Apply Arabic diacritization to a given draft."""
    draft = await get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    body = payload.body if payload.body is not None else draft.body or ""
    next_body, replace_range = apply_tashkeel_to_body(body, payload.selection)

    try:
        updated = await update_draft(
            draft_id,
            body=next_body,
            client_revision=payload.clientRevision,
        )
    except RevisionConflictError as error:
        return conflict_response(error)

    if not updated or updated.body is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update draft",
        )
    return TashkeelResponse(
        draftBody=updated.body,
        replaceRange=replace_range,
        persistedRevision=updated.revision,
    )
