"""Draft CRUD routers.

Provides endpoints to list, create, retrieve, and update drafts.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from src.api.services.drafts import (
    create_draft,
    delete_draft,
    get_draft,
    list_drafts,
    update_draft,
)

router = APIRouter()


class DraftCreateRequest(BaseModel):
    """Draft creation request."""

    title: str | None = None
    body: str | None = None


class DraftUpdateRequest(BaseModel):
    """Draft update request."""

    title: str | None = None
    body: str | None = None
    clientRevision: int | None = None


class DraftResponse(BaseModel):
    """Draft response model."""

    id: str
    title: str | None
    body: str | None
    stageLabel: str | None
    updatedAt: str | None
    savedAt: str | None
    revision: int
    formatting: dict = Field(default_factory=dict)
    corrections: list[dict] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DraftSummaryResponse(BaseModel):
    """Draft summary model used by the list endpoint."""

    id: str
    title: str
    stageLabel: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True)


class DraftUpdateResponse(BaseModel):
    """Draft update response expected by the frontend contract."""

    draft: DraftResponse
    persistedRevision: int
    savedAt: str


@router.get("", response_model=list[DraftSummaryResponse])
async def list_all_drafts():
    """List all drafts."""
    drafts = await list_drafts()
    return drafts


@router.post("", response_model=DraftResponse, status_code=status.HTTP_201_CREATED)
async def create_new_draft(payload: DraftCreateRequest):
    """Create a new draft."""
    draft = await create_draft(title=payload.title, body=payload.body)
    return draft


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft_by_id(draft_id: str):
    """Get a draft by its ID."""
    draft = await get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.patch("/{draft_id}", response_model=DraftUpdateResponse)
async def update_existing_draft(draft_id: str, payload: DraftUpdateRequest):
    """Update an existing draft."""
    draft = await update_draft(draft_id, title=payload.title, body=payload.body)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return DraftUpdateResponse(
        draft=draft,
        persistedRevision=draft.revision,
        savedAt=draft.savedAt or "",
    )


# Delete a draft
@router.delete("/{draft_id}", status_code=204)
async def delete_existing_draft(draft_id: str):
    """Delete a draft by its ID.
    Returns HTTP 204 No Content on success.
    """
    deleted = await delete_draft(draft_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Draft not found")
    # No content response
    return
