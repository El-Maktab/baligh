"""Router for the analysis endpoint."""

import uuid

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger
from src.api.services.corrections import run as corrections_run
from src.api.services.drafts import RevisionConflictError, get_draft, update_draft
from src.api.services.editor_contract import (
    AnalyzeRequest,
    AnalyzeResponse,
    RevisionConflictPayload,
    get_correction_counts,
    normalize_candidate_edit,
    normalize_error_detection,
)
from src.services.ged.schemas import ErrorSpan
from starlette.concurrency import run_in_threadpool

router = APIRouter()


def _find_matching_error(ged_output, candidate) -> ErrorSpan | None:
    """Pick the closest GED error span for a candidate edit."""
    errors = getattr(ged_output, "errors", [])
    for error in errors:
        if tuple(getattr(error, "span", ())) == tuple(candidate.span):
            return error
    for error in errors:
        error_tokens = set(getattr(error, "token_refs", []))
        if error_tokens.intersection(candidate.token_refs):
            return error
    return None


def _error_key(error) -> tuple:
    """Build a stable key for matching GED detections."""
    return (
        tuple(getattr(error, "span", ())),
        tuple(getattr(error, "token_refs", [])),
        getattr(getattr(error, "category", None), "value", None),
        getattr(error, "subtype", None),
    )


def conflict_response(error: RevisionConflictError) -> JSONResponse:
    """Build a 409 payload the frontend can hydrate directly."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=RevisionConflictPayload(latestDraft=error.latest_draft).model_dump(
            mode="json"
        ),
    )


@router.post("/{draft_id}/analyze", response_model=AnalyzeResponse)
async def analyze_draft(draft_id: str, payload: AnalyzeRequest):
    """Analyze a draft, persist corrections, and return normalized results."""
    draft = await get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    body = payload.body if payload.body is not None else draft.body or ""
    gec_output, ged_output = await run_in_threadpool(corrections_run, body)

    logger.debug(
        "GEC output: {}, GED output: {}",
        gec_output.model_dump(),
        ged_output.model_dump(),
    )
    normalized_corrections: list[dict] = []
    matched_error_keys: set[tuple] = set()
    for candidate in gec_output.ranked_edits:
        error_span = _find_matching_error(ged_output, candidate)
        if error_span is not None:
            matched_error_keys.add(_error_key(error_span))
        normalized = normalize_candidate_edit(
            correction_id=f"corr-{uuid.uuid4()}",
            body=body,
            candidate=candidate,
            module_name=candidate.selected_module,
            error_span=error_span,
        )
        normalized_corrections.append(normalized)

    for error_span in ged_output.errors:
        if _error_key(error_span) in matched_error_keys:
            continue
        normalized_corrections.append(
            normalize_error_detection(
                detection_id=f"det-{uuid.uuid4()}",
                body=body,
                error_span=error_span,
            )
        )

    if payload.categories:
        allowed = {category.value for category in payload.categories}
        normalized_corrections = [
            correction
            for correction in normalized_corrections
            if correction["bucket"] in allowed
        ]

    try:
        updated = await update_draft(
            draft_id,
            body=body,
            corrections=normalized_corrections,
            client_revision=payload.clientRevision,
        )
    except RevisionConflictError as error:
        return conflict_response(error)

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update draft",
        )

    return AnalyzeResponse(
        analysisRevision=updated.revision,
        corrections=normalized_corrections,
        counts=get_correction_counts(normalized_corrections),
    )
