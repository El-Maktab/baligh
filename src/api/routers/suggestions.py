"""Router for next-word suggestions (NWS).

It receives a request payload, runs the NWS service and returns the suggestions.
"""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.api.services.drafts import get_draft
from src.api.services.nws import run as nws_run
from src.services.nws.schemas import Suggestion

router = APIRouter()


class SuggestionsRequest(BaseModel):
    """Request model for next-word suggestions."""

    body: str
    selection: str | None = None
    caret: int | None = None
    clientRevision: int | None = None
    mode: Literal["NWP", "WAC"]
    top_k: int | None = 5


class SuggestionsResponse(BaseModel):
    """Response model for next-word suggestions."""

    mode: str
    suggestions: list[Suggestion]


@router.post("/{draft_id}/suggestions", response_model=SuggestionsResponse)
async def get_suggestions(draft_id: str, payload: SuggestionsRequest):
    """Get next-word suggestions for a given draft."""
    draft = await get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    preproc_output = type(
        "Obj",
        (),
        {"tokens": [], "morph_features": [], "current_fragment": payload.body},
    )
    nws_output = nws_run(preproc_output, mode=payload.mode, top_k=payload.top_k or 5)
    suggestions = [s for s in nws_output.suggestions]
    return SuggestionsResponse(mode=nws_output.mode, suggestions=suggestions)
