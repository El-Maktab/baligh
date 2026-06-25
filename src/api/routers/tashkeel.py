"""Router for Arabic diacritization (tashkeel).

Currently a stub implementation that returns the original body unchanged.
In a full implementation this would call the dictionary GEC module to add
diacritics to the selected fragment.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from src.api.services.drafts import get_draft, update_draft

router = APIRouter()


class TashkeelRequest(BaseModel):
    """Request model for Arabic diacritization."""

    body: str
    selection: str | None = None
    clientRevision: int | None = None


class TashkeelResponse(BaseModel):
    """Response model for Arabic diacritization."""

    draftBody: str
    replaceRange: list = Field(default_factory=list)
    persistedRevision: int


@router.post("/{draft_id}/tashkeel", response_model=TashkeelResponse)
async def apply_tashkeel(draft_id: str, payload: TashkeelRequest):
    """Apply Arabic diacritization to a given draft."""
    draft = await get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    updated = await update_draft(draft_id, body=payload.body)
    if not updated or not updated.body:
        raise HTTPException(status_code=500, detail="Failed to update draft")
    return TashkeelResponse(
        draftBody=updated.body,
        replaceRange=[],
        persistedRevision=updated.revision,
    )
