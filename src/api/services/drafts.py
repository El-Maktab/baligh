"""Draft repository using Motor (async MongoDB)."""

import uuid
from datetime import UTC, datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument

from ..config import settings
from .editor_contract import (
    CorrectionStatus,
    DraftResponse,
    draft_to_response,
    normalize_selection,
    normalize_stored_correction,
    replace_text_range,
    resolve_corrections,
)


class RevisionConflictError(Exception):
    """Raised when the client revision is stale."""

    def __init__(self, latest_draft: DraftResponse):
        super().__init__("Revision conflict")
        self.latest_draft = latest_draft


class CorrectionNotAvailableError(Exception):
    """Raised when a correction is missing or stale."""

    def __init__(self, latest_draft: DraftResponse):
        super().__init__("Correction not available")
        self.latest_draft = latest_draft


class DraftDocument(BaseModel):
    """Model for representing a draft document."""

    id: str = Field(..., alias="id")
    title: str | None = None
    body: str | None = None
    stageLabel: str | None = None
    updatedAt: str | None = None
    savedAt: str | None = None
    revision: int = 0
    formatting: dict = Field(default_factory=dict)
    corrections: list[dict] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


DEFAULT_DRAFT_TITLE = "مسودة جديدة"
DEFAULT_DRAFT_BODY = "اكتب النص هنا..."
DEFAULT_STAGE_LABEL = "جاهز للربط"
_mongo_client: AsyncIOMotorClient | None = None


def _now_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat()


def _default_formatting() -> dict[str, Any]:
    """Return the default editor formatting payload."""
    return {
        "strong": [],
        "emphasis": [],
        "lines": {},
    }


def _normalize_draft_payload(doc: dict[str, Any]) -> DraftDocument:
    """Normalize a draft document read from MongoDB."""
    body = doc.get("body") or ""
    normalized = {
        "id": doc["id"],
        "title": doc.get("title") or DEFAULT_DRAFT_TITLE,
        "body": body,
        "stageLabel": doc.get("stageLabel") or DEFAULT_STAGE_LABEL,
        "updatedAt": doc.get("updatedAt") or "الآن",
        "savedAt": doc.get("savedAt") or _now_iso(),
        "revision": doc.get("revision", 1),
        "formatting": doc.get("formatting") or _default_formatting(),
        "corrections": [
            normalize_stored_correction(body, correction)
            for correction in (doc.get("corrections") or [])
        ],
    }
    return DraftDocument(**normalized)


def _build_seed_draft() -> DraftDocument:
    """Create the default draft inserted into an empty database."""
    timestamp = _now_iso()
    return DraftDocument(
        id=f"draft-{uuid.uuid4()}",
        title=DEFAULT_DRAFT_TITLE,
        body=DEFAULT_DRAFT_BODY,
        stageLabel=DEFAULT_STAGE_LABEL,
        updatedAt="الآن",
        savedAt=timestamp,
        revision=1,
        formatting=_default_formatting(),
        corrections=[],
    )


def init_mongo_client(client: AsyncIOMotorClient) -> None:
    """Register the shared Motor client for repository calls."""
    global _mongo_client
    _mongo_client = client


def close_mongo_client() -> None:
    """Close and clear the shared Motor client when this module owns it."""
    global _mongo_client
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None


def _get_client() -> AsyncIOMotorClient:
    """Return the shared Motor client, creating one lazily if needed."""
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(settings.mongodb_uri)
    return _mongo_client


def _get_collection():
    """Get the drafts collection."""
    db = _get_client().get_default_database()
    return db["drafts"]


async def list_drafts() -> list[DraftDocument]:
    """List all drafts."""
    coll = _get_collection()
    cursor = coll.find({}, {"_id": 0}).sort("savedAt", -1)
    drafts = []
    async for doc in cursor:
        drafts.append(_normalize_draft_payload(doc))
    return drafts


async def create_draft(
    title: str | None = None, body: str | None = None
) -> DraftDocument:
    """Create a new draft."""
    coll = _get_collection()
    timestamp = _now_iso()
    draft = DraftDocument(
        id=f"draft-{uuid.uuid4()}",
        title=title or DEFAULT_DRAFT_TITLE,
        body=body if body is not None else DEFAULT_DRAFT_BODY,
        stageLabel=DEFAULT_STAGE_LABEL,
        updatedAt="الآن",
        savedAt=timestamp,
        revision=1,
        formatting=_default_formatting(),
        corrections=[],
    )
    await coll.insert_one(draft.model_dump(by_alias=True, exclude_none=True))
    return draft


async def get_draft(draft_id: str) -> DraftDocument | None:
    """Get a draft by its ID."""
    coll = _get_collection()
    doc = await coll.find_one({"id": draft_id}, {"_id": 0})
    if doc:
        return _normalize_draft_payload(doc)
    return None


async def update_draft(
    draft_id: str,
    title: str | None = None,
    body: str | None = None,
    formatting: dict[str, Any] | None = None,
    corrections: list[dict] | None = None,
    client_revision: int | None = None,
) -> DraftDocument | None:
    """Update a draft."""
    coll = _get_collection()
    current = await coll.find_one({"id": draft_id}, {"_id": 0})
    if not current:
        return None
    if client_revision is not None and client_revision != current.get("revision", 1):
        raise RevisionConflictError(
            draft_to_response(_normalize_draft_payload(current))
        )

    draft = _normalize_draft_payload(current)
    next_title = draft.title if title is None else title
    next_body = draft.body if body is None else body
    next_formatting = draft.formatting if formatting is None else formatting
    next_corrections = draft.corrections if corrections is None else corrections

    if body is not None and body != draft.body:
        next_corrections = resolve_corrections(draft.body or "", body, next_corrections)

    content_changed = next_title != draft.title or next_body != draft.body
    changed = (
        content_changed
        or next_formatting != draft.formatting
        or next_corrections != draft.corrections
    )
    if not changed:
        return draft

    update_payload = {
        "title": next_title,
        "body": next_body,
        "formatting": next_formatting,
        "corrections": next_corrections,
    }
    if content_changed:
        update_payload["updatedAt"] = "الآن"
        update_payload["savedAt"] = _now_iso()

    update_ops: dict[str, Any] = {"$set": update_payload}
    if content_changed:
        update_ops["$inc"] = {"revision": 1}
    result = await coll.find_one_and_update(
        {"id": draft_id},
        update_ops,
        return_document=ReturnDocument.AFTER,
        projection={"_id": 0},
    )
    if result:
        return _normalize_draft_payload(result)
    return None


async def apply_correction(
    draft_id: str,
    correction_id: str,
    client_revision: int | None = None,
    body: str | None = None,
) -> DraftDocument | None:
    """Apply a correction replacement to the draft body."""
    coll = _get_collection()
    current = await coll.find_one(
        {"id": draft_id},
        {
            "_id": 0,
            "id": 1,
            "title": 1,
            "body": 1,
            "stageLabel": 1,
            "updatedAt": 1,
            "savedAt": 1,
            "revision": 1,
            "formatting": 1,
            "corrections": 1,
        },
    )
    if not current:
        return None
    draft = _normalize_draft_payload(current)
    if client_revision is not None and client_revision != draft.revision:
        raise RevisionConflictError(draft_to_response(draft))

    next_body = body if body is not None else draft.body or ""
    next_corrections = draft.corrections
    if next_body != (draft.body or ""):
        next_corrections = resolve_corrections(
            draft.body or "", next_body, next_corrections
        )

    correction = next(
        (entry for entry in next_corrections if entry.get("id") == correction_id),
        None,
    )
    if (
        not correction
        or correction.get("status") == CorrectionStatus.STALE.value
        or correction.get("kind") == "detection"
        or correction.get("actionable") is False
    ):
        raise CorrectionNotAvailableError(
            draft_to_response(
                draft.model_copy(
                    update={"body": next_body, "corrections": next_corrections}
                )
            )
        )

    span = normalize_selection(correction["span"])
    if next_body[span.start : span.end] != correction.get("original", ""):
        refreshed = draft.model_copy(
            update={"body": next_body, "corrections": next_corrections}
        )
        raise CorrectionNotAvailableError(draft_to_response(refreshed))

    updated_body = replace_text_range(
        next_body, span, correction.get("replacement", "")
    )
    delta = len(correction.get("replacement", "")) - (span.end - span.start)
    updated_corrections = []
    for entry in next_corrections:
        if entry.get("id") == correction_id:
            updated_corrections.append(
                {**entry, "status": CorrectionStatus.ACCEPTED.value}
            )
            continue
        entry_span = entry.get("span", {})
        if (
            entry.get("status") == CorrectionStatus.ACTIVE.value
            and entry_span.get("start", 0) >= span.end
        ):
            updated_corrections.append(
                {
                    **entry,
                    "span": {
                        "start": entry_span["start"] + delta,
                        "end": entry_span["end"] + delta,
                    },
                }
            )
            continue
        updated_corrections.append(entry)

    await coll.update_one(
        {"id": draft_id},
        {
            "$set": {
                "body": updated_body,
                "corrections": updated_corrections,
                "updatedAt": "الآن",
                "savedAt": _now_iso(),
            },
            "$inc": {"revision": 1},
        },
    )
    updated = await coll.find_one({"id": draft_id}, {"_id": 0})
    if updated:
        return _normalize_draft_payload(updated)
    return None


async def delete_draft(draft_id: str) -> bool:
    """Delete a draft by its ID.
    Returns True if a document was deleted, False otherwise.
    """
    coll = _get_collection()
    result = await coll.delete_one({"id": draft_id})
    return result.deleted_count > 0


async def ignore_correction(
    draft_id: str,
    correction_id: str,
    client_revision: int | None = None,
) -> DraftDocument | None:
    """Ignore a correction."""
    coll = _get_collection()
    current = await coll.find_one({"id": draft_id}, {"_id": 0})
    if not current:
        return None
    draft = _normalize_draft_payload(current)
    if client_revision is not None and client_revision != draft.revision:
        raise RevisionConflictError(draft_to_response(draft))

    updated_corrections = []
    found = False
    for correction in draft.corrections:
        if correction.get("id") == correction_id:
            updated_corrections.append(
                {**correction, "status": CorrectionStatus.IGNORED.value}
            )
            found = True
        else:
            updated_corrections.append(correction)
    if not found:
        raise CorrectionNotAvailableError(draft_to_response(draft))

    await coll.update_one(
        {"id": draft_id},
        {
            "$set": {
                "corrections": updated_corrections,
                "updatedAt": "الآن",
                "savedAt": _now_iso(),
            },
            "$inc": {"revision": 1},
        },
    )
    updated = await coll.find_one({"id": draft_id}, {"_id": 0})
    if updated:
        return _normalize_draft_payload(updated)
    return None


async def seed_default_draft() -> DraftDocument | None:
    """Seed a default draft when the collection is empty."""
    coll = _get_collection()
    if await coll.count_documents({}, limit=1) > 0:
        return None

    draft = _build_seed_draft()
    await coll.insert_one(draft.model_dump(by_alias=True, exclude_none=True))
    return draft
