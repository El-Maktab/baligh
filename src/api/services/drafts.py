"""Draft repository using Motor (async MongoDB).

Provides CRUD operations for draft documents.
"""

import uuid

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

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

    class Config:
        """Configuration for the DraftDocument model."""

        allow_population_by_field_name = True
        arbitrary_types_allowed = True


def _get_collection():
    """Get the drafts collection."""
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client.get_default_database()
    return db["drafts"]


async def list_drafts() -> list[DraftDocument]:
    """List all drafts."""
    coll = _get_collection()
    cursor = coll.find(
        {}, {"_id": 0, "id": 1, "title": 1, "stageLabel": 1, "updatedAt": 1}
    )
    drafts = []
    async for doc in cursor:
        drafts.append(DraftDocument(**doc))
    return drafts


async def create_draft(
    title: str | None = None, body: str | None = None
) -> DraftDocument:
    """Create a new draft."""
    coll = _get_collection()
    draft_id = f"draft-{uuid.uuid4()}"
    draft = DraftDocument(
        id=draft_id,
        title=title,
        body=body,
        stageLabel="",
        updatedAt=None,
        savedAt=None,
        revision=1,
        formatting={},
        corrections=[],
    )
    await coll.insert_one(draft.dict(by_alias=True, exclude_none=True))
    return draft


async def get_draft(draft_id: str) -> DraftDocument | None:
    """Get a draft by its ID."""
    coll = _get_collection()
    doc = await coll.find_one({"id": draft_id}, {"_id": 0})
    if doc:
        return DraftDocument(**doc)
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
    if title is not None:
        update_fields["title"] = title
    if body is not None:
        update_fields["body"] = body
    update_ops: dict = {}
    if update_fields:
        update_ops["$set"] = update_fields
    if corrections is not None:
        if "$set" not in update_ops:
            update_ops["$set"] = {}
        update_ops["$set"]["corrections"] = corrections

    if not update_ops:
        return await get_draft(draft_id)

    update_ops["$inc"] = {"revision": 1}
    result = await coll.find_one_and_update(
        {"id": draft_id},
        update_ops,
        return_document=True,
        projection={"_id": 0},
    )
    if result:
        return DraftDocument(**result)
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
    start, end = corr.get("span", [0, 0])
    new_body = draft["body"][:start] + replacement + draft["body"][end:]
    # Remove the accepted correction from the list and keep other corrections unchanged.
    updated_corrections = [c for c in draft["corrections"] if c.get("id") != correction_id]
    await coll.update_one(
        {"id": draft_id},
        {
            "$set": {"body": new_body, "corrections": updated_corrections},
            "$inc": {"revision": 1},
        },
    )
    updated = await coll.find_one({"id": draft_id}, {"_id": 0})
    if updated:
        return DraftDocument(**updated)
    return None


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
        {"$set": {"corrections": draft["corrections"]}, "$inc": {"revision": 1}},
    )
    updated = await coll.find_one({"id": draft_id}, {"_id": 0})
    if updated:
        return DraftDocument(**updated)
    return None
