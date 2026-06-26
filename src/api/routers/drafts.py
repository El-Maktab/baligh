"""Draft CRUD routers."""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from src.api.services.drafts import (
    RevisionConflictError,
    create_draft,
    delete_draft,
    get_draft,
    list_drafts,
    update_draft,
)
from src.api.services.editor_contract import (
    DraftCreateRequest,
    DraftResponse,
    DraftSummaryResponse,
    DraftUpdateRequest,
    DraftUpdateResponse,
    RevisionConflictPayload,
    draft_to_response,
    summarize_draft,
)

router = APIRouter()


def conflict_response(error: RevisionConflictError) -> JSONResponse:
    """Build a 409 payload the frontend can hydrate directly."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=RevisionConflictPayload(latestDraft=error.latest_draft).model_dump(
            mode="json"
        ),
    )


@router.get("", response_model=list[DraftSummaryResponse])
async def list_all_drafts():
    """List all drafts."""
    drafts = await list_drafts()
    return [summarize_draft(draft) for draft in drafts]


@router.post("", response_model=DraftResponse, status_code=status.HTTP_201_CREATED)
async def create_new_draft(payload: DraftCreateRequest):
    """Create a new draft."""
    draft = await create_draft(title=payload.title, body=payload.body)
    return draft_to_response(draft)


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft_by_id(draft_id: str):
    """Get a draft by its ID."""
    draft = await get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft_to_response(draft)


@router.patch("/{draft_id}", response_model=DraftUpdateResponse)
async def update_existing_draft(draft_id: str, payload: DraftUpdateRequest):
    """Update an existing draft."""
    try:
        draft = await update_draft(
            draft_id,
            title=payload.title,
            body=payload.body,
            formatting=payload.formatting,
            client_revision=payload.clientRevision,
        )
    except RevisionConflictError as error:
        return conflict_response(error)

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return DraftUpdateResponse(
        draft=draft_to_response(draft),
        persistedRevision=draft.revision,
        savedAt=draft.savedAt or "",
    )


@router.delete("/{draft_id}", status_code=204)
async def delete_existing_draft(draft_id: str):
    """Delete a draft by its ID."""
    deleted = await delete_draft(draft_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Draft not found")
    return None
