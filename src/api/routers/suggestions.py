"""Router for editor suggestions."""

from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from src.api.services.drafts import RevisionConflictError, get_draft
from src.api.services.editor_contract import (
    RevisionConflictPayload,
    SuggestionItem,
    SuggestionMode,
    SuggestionRequest,
    SuggestionResponse,
    draft_to_response,
    normalize_nws_suggestion,
)
from src.api.services.nws import run as nws_run

router = APIRouter()

ARABIC_WORD_RE = re.compile(r"[\u0621-\u063a\u0641-\u064a]+$")
ARABIC_SUFFIX_RE = re.compile(r"^[\u0621-\u063a\u0641-\u064a]*")


def conflict_response(error: RevisionConflictError) -> JSONResponse:
    """Build a 409 payload the frontend can hydrate directly."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=RevisionConflictPayload(latestDraft=error.latest_draft).model_dump(
            mode="json"
        ),
    )


def create_word_suggestions(prefix: str, limit: int) -> list[str]:
    """Fallback word completions when the NWS service has no results."""
    dictionary = [
        "المحبة",
        "المحرر",
        "المراجعة",
        "المعنى",
        "الصفحة",
        "الفريق",
        "الصياغة",
    ]
    matches = [entry for entry in dictionary if entry.startswith(prefix)]
    if matches:
        return matches[:limit]
    return [f"{prefix}ة", f"{prefix}ات"][:limit]


def build_fallback_suggestions(payload: SuggestionRequest) -> SuggestionResponse:
    """Build deterministic fallback suggestions for the editor."""
    before_caret = payload.body[: payload.caret]
    after_caret = payload.body[payload.caret :]
    word_match = ARABIC_WORD_RE.search(before_caret)

    if payload.mode == SuggestionMode.WORD and word_match:
        prefix = word_match.group(0)
        start = payload.caret - len(prefix)
        suffix = ARABIC_SUFFIX_RE.search(after_caret)
        end = payload.caret + len(suffix.group(0) if suffix else "")
        suggestions = [
            SuggestionItem(
                id=f"word-{index}",
                label=entry,
                displayText=entry,
                insertText=entry,
                kind=SuggestionMode.WORD,
            )
            for index, entry in enumerate(
                create_word_suggestions(prefix, payload.limit)
            )
        ]
        return SuggestionResponse(
            suggestionSessionId=f"suggest-{uuid.uuid4()}",
            mode=SuggestionMode.WORD,
            replaceRange={"start": start, "end": end},
            suggestions=suggestions,
        )

    continuations = [
        " لذلك أراجع الصياغة قبل الإرسال.",
        " ثم أعود لتنقيح الجملة التالية.",
        " وهذا يمنح النص إيقاعاً أوضح.",
    ]
    suggestions = [
        SuggestionItem(
            id=f"sentence-{index}",
            label=entry.strip(),
            displayText=entry,
            insertText=entry,
            kind=SuggestionMode.SENTENCE,
        )
        for index, entry in enumerate(continuations[: payload.limit])
    ]
    return SuggestionResponse(
        suggestionSessionId=f"suggest-{uuid.uuid4()}",
        mode=SuggestionMode.SENTENCE,
        replaceRange={"start": payload.caret, "end": payload.caret},
        suggestions=suggestions,
    )


@router.post("/{draft_id}/suggestions", response_model=SuggestionResponse)
async def get_suggestions(draft_id: str, payload: SuggestionRequest):
    """Get normalized suggestions for a given draft."""
    draft = await get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if payload.clientRevision is not None and payload.clientRevision != draft.revision:
        return conflict_response(
            RevisionConflictError(latest_draft=draft_to_response(draft))
        )

    preproc_output = type(
        "Obj",
        (),
        {"tokens": [], "morph_features": [], "current_fragment": payload.body},
    )
    nws_output = nws_run(
        preproc_output,
        mode="WAC" if payload.mode == SuggestionMode.WORD else "NWP",
        top_k=payload.limit,
    )
    if not nws_output.suggestions:
        return build_fallback_suggestions(payload)

    normalized = [
        normalize_nws_suggestion(suggestion, index, payload.mode)
        for index, suggestion in enumerate(nws_output.suggestions[: payload.limit])
    ]
    replace_range = build_fallback_suggestions(payload).replaceRange
    return SuggestionResponse(
        suggestionSessionId=f"suggest-{uuid.uuid4()}",
        mode=payload.mode,
        replaceRange=replace_range,
        suggestions=normalized,
    )
