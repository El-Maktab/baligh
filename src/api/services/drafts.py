"""Draft repository using Motor (async MongoDB).

Provides CRUD operations for draft documents.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument

from ..config import settings


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
    normalized = {
        "id": doc["id"],
        "title": doc.get("title") or DEFAULT_DRAFT_TITLE,
        "body": doc.get("body") or "",
        "stageLabel": doc.get("stageLabel") or DEFAULT_STAGE_LABEL,
        "updatedAt": doc.get("updatedAt") or "الآن",
        "savedAt": doc.get("savedAt") or _now_iso(),
        "revision": doc.get("revision", 1),
        "formatting": doc.get("formatting") or _default_formatting(),
        "corrections": doc.get("corrections") or [],
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


def _get_collection():
    """Get the drafts collection."""
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client.get_default_database()
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
    corrections: list[dict] | None = None,
) -> DraftDocument | None:
    """Update a draft."""
    coll = _get_collection()
    update_fields = {}
    touched_content = False
    if title is not None:
        update_fields["title"] = title
        touched_content = True
    if body is not None:
        update_fields["body"] = body
        touched_content = True
    update_ops: dict = {}
    if update_fields:
        update_ops["$set"] = update_fields
    if corrections is not None:
        if "$set" not in update_ops:
            update_ops["$set"] = {}
        update_ops["$set"]["corrections"] = corrections
        touched_content = True

    if not update_ops:
        return await get_draft(draft_id)

    if touched_content:
        update_ops.setdefault("$set", {})
        update_ops["$set"]["updatedAt"] = "الآن"
        update_ops["$set"]["savedAt"] = _now_iso()

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
    draft_id: str, correction_id: str, replacement: str
) -> DraftDocument | None:
    """Replace the text span of a correction with 'replacement'.

    The original correction dict must contain ``span``: [start, end].
    """
    coll = _get_collection()
    draft = await coll.find_one(
        {"id": draft_id}, {"_id": 0, "body": 1, "corrections": 1, "revision": 1}
    )
    if not draft:
        return None
    corr = next((c for c in draft["corrections"] if c.get("id") == correction_id), None)
    if not corr:
        return None
    span = corr.get("span", {})
    if isinstance(span, dict):
        start = span.get("start", 0)
        end = span.get("end", 0)
    else:
        start, end = span
    new_body = draft["body"][:start] + replacement + draft["body"][end:]
    # Remove the accepted correction from the list and keep other corrections unchanged.
    updated_corrections = [
        c for c in draft["corrections"] if c.get("id") != correction_id
    ]
    await coll.update_one(
        {"id": draft_id},
        {
            "$set": {
                "body": new_body,
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


async def ignore_correction(draft_id: str, correction_id: str) -> DraftDocument | None:
    """Ignore a correction."""
    coll = _get_collection()
    draft = await coll.find_one({"id": draft_id}, {"_id": 0, "corrections": 1})
    if not draft:
        return None
    for c in draft["corrections"]:
        if c.get("id") == correction_id:
            c["status"] = "ignored"
    await coll.update_one(
        {"id": draft_id},
        {
            "$set": {
                "corrections": draft["corrections"],
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
