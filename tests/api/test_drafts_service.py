import pytest
from src.api.services.drafts import (
    DEFAULT_DRAFT_BODY,
    DEFAULT_DRAFT_TITLE,
    DEFAULT_STAGE_LABEL,
    CorrectionNotAvailableError,
    RevisionConflictError,
    _build_seed_draft,
    _normalize_draft_payload,
    apply_correction,
    ignore_correction,
    update_draft,
)
from src.api.services.editor_contract import get_correction_counts


class FakeDraftsCollection:
    def __init__(self, doc):
        self.doc = doc.copy()

    async def find_one(self, query, projection=None):
        if query.get("id") != self.doc["id"]:
            return None
        result = self.doc.copy()
        if projection:
            result = {
                key: value
                for key, value in result.items()
                if projection.get(key, 1) and key != "_id"
            }
        return result

    async def find_one_and_update(
        self, query, update, return_document=None, projection=None
    ):
        found = await self.find_one(query, projection=None)
        if not found:
            return None
        self._apply_update(update)
        return await self.find_one(query, projection)

    async def update_one(self, query, update):
        found = await self.find_one(query, projection=None)
        if not found:
            return None
        self._apply_update(update)
        return None

    def _apply_update(self, update):
        for key, value in update.get("$set", {}).items():
            self.doc[key] = value
        for key, value in update.get("$inc", {}).items():
            self.doc[key] = self.doc.get(key, 0) + value


def _fake_collection(monkeypatch, doc):
    collection = FakeDraftsCollection(doc)
    monkeypatch.setattr("src.api.services.drafts._get_collection", lambda: collection)
    return collection


def test_build_seed_draft_uses_frontend_friendly_defaults():
    draft = _build_seed_draft()

    assert draft.title == DEFAULT_DRAFT_TITLE
    assert draft.body == DEFAULT_DRAFT_BODY
    assert draft.stageLabel == DEFAULT_STAGE_LABEL
    assert draft.updatedAt == "الآن"
    assert draft.savedAt is not None
    assert draft.formatting == {"strong": [], "emphasis": [], "lines": {}}
    assert draft.corrections == []


def test_normalize_draft_payload_fills_missing_fields():
    draft = _normalize_draft_payload({"id": "draft-1"})

    assert draft.id == "draft-1"
    assert draft.title == DEFAULT_DRAFT_TITLE
    assert draft.body == ""
    assert draft.stageLabel == DEFAULT_STAGE_LABEL
    assert draft.updatedAt == "الآن"
    assert draft.savedAt is not None
    assert draft.revision == 1
    assert draft.formatting == {"strong": [], "emphasis": [], "lines": {}}
    assert draft.corrections == []


def test_normalize_draft_payload_preserves_detection_only_findings():
    draft = _normalize_draft_payload(
        {
            "id": "draft-1",
            "body": "هذه جملة تنتفخ.",
            "corrections": [
                {
                    "id": "det-1",
                    "kind": "detection",
                    "actionable": False,
                    "category": "grammar",
                    "bucket": "grammar",
                    "status": "active",
                    "span": {"start": 9, "end": 15},
                    "title": "رصد نحوي",
                    "lineLabel": "السطر 1",
                    "original": "تنتفخ",
                    "replacement": None,
                    "explanation": "شرح",
                    "ruleLabel": "قاعدة",
                    "taxonomyCode": "SY:review_only",
                    "taxonomyLabel": "review only",
                    "sourceModule": "rule_based",
                }
            ],
        }
    )

    assert draft.corrections[0]["kind"] == "detection"
    assert draft.corrections[0]["actionable"] is False
    assert draft.corrections[0]["replacement"] is None


@pytest.mark.asyncio
async def test_update_draft_rejects_stale_revision(monkeypatch):
    _fake_collection(
        monkeypatch,
        {
            "id": "draft-1",
            "title": "عنوان",
            "body": "النص",
            "stageLabel": DEFAULT_STAGE_LABEL,
            "updatedAt": "الآن",
            "savedAt": "2026-01-01T00:00:00Z",
            "revision": 3,
            "formatting": {"strong": [], "emphasis": [], "lines": {}},
            "corrections": [],
        },
    )

    try:
        await update_draft("draft-1", title="جديد", client_revision=2)
    except RevisionConflictError as error:
        assert error.latest_draft.revision == 3
        assert error.latest_draft.title == "عنوان"
    else:
        raise AssertionError("Expected a revision conflict")


@pytest.mark.asyncio
async def test_apply_and_ignore_correction_return_frontend_friendly_state(monkeypatch):
    body = "هذا النص يحتوى على خطأ."
    start = body.index("يحتوى")
    _fake_collection(
        monkeypatch,
        {
            "id": "draft-1",
            "title": "عنوان",
            "body": body,
            "stageLabel": DEFAULT_STAGE_LABEL,
            "updatedAt": "الآن",
            "savedAt": "2026-01-01T00:00:00Z",
            "revision": 4,
            "formatting": {"strong": [], "emphasis": [], "lines": {}},
            "corrections": [
                {
                    "id": "corr-1",
                    "category": "spelling",
                    "bucket": "spelling",
                    "status": "active",
                    "span": {"start": start, "end": start + len("يحتوى")},
                    "title": "تصحيح إملائي",
                    "lineLabel": "السطر 1",
                    "original": "يحتوى",
                    "replacement": "يحتوي",
                    "explanation": "شرح",
                    "ruleLabel": "قاعدة",
                    "taxonomyCode": "OT:ya",
                    "taxonomyLabel": "ya",
                    "sourceModule": "DICTIONARY",
                }
            ],
        },
    )

    accepted = await apply_correction("draft-1", "corr-1", client_revision=4)
    assert accepted is not None
    assert accepted.body == "هذا النص يحتوي على خطأ."
    assert accepted.corrections[0]["status"] == "accepted"
    assert get_correction_counts(accepted.corrections) == {
        "all": 0,
        "spelling": 0,
        "grammar": 0,
        "style": 0,
    }

    ignored = await ignore_correction("draft-1", "corr-1", client_revision=5)
    assert ignored is not None
    assert ignored.corrections[0]["status"] == "ignored"


@pytest.mark.asyncio
async def test_update_draft_does_not_bump_revision_for_corrections_only(monkeypatch):
    _fake_collection(
        monkeypatch,
        {
            "id": "draft-1",
            "title": "عنوان",
            "body": "النص",
            "stageLabel": DEFAULT_STAGE_LABEL,
            "updatedAt": "الآن",
            "savedAt": "2026-01-01T00:00:00Z",
            "revision": 3,
            "formatting": {"strong": [], "emphasis": [], "lines": {}},
            "corrections": [],
        },
    )

    updated = await update_draft(
        "draft-1",
        corrections=[
            {
                "id": "corr-1",
                "category": "style",
                "bucket": "style",
                "status": "active",
                "span": {"start": 0, "end": 2},
                "title": "تحسين أسلوبي",
                "lineLabel": "السطر 1",
                "original": "الن",
                "replacement": "هذا",
                "explanation": "شرح",
                "ruleLabel": "قاعدة",
                "taxonomyCode": "legacy:style",
                "taxonomyLabel": "style",
                "sourceModule": "TAG",
            }
        ],
        client_revision=3,
    )

    assert updated is not None
    assert updated.revision == 3
    assert len(updated.corrections) == 1


@pytest.mark.asyncio
async def test_apply_correction_raises_conflict_when_span_is_stale(monkeypatch):
    body = "هذا النص يحتوى على خطأ."
    start = body.index("يحتوى")
    _fake_collection(
        monkeypatch,
        {
            "id": "draft-1",
            "title": "عنوان",
            "body": body,
            "stageLabel": DEFAULT_STAGE_LABEL,
            "updatedAt": "الآن",
            "savedAt": "2026-01-01T00:00:00Z",
            "revision": 4,
            "formatting": {"strong": [], "emphasis": [], "lines": {}},
            "corrections": [
                {
                    "id": "corr-1",
                    "category": "spelling",
                    "bucket": "spelling",
                    "status": "stale",
                    "span": {"start": start, "end": start + len("يحتوى")},
                    "title": "تصحيح إملائي",
                    "lineLabel": "السطر 1",
                    "original": "يحتوى",
                    "replacement": "يحتوي",
                    "explanation": "شرح",
                    "ruleLabel": "قاعدة",
                    "taxonomyCode": "OT:ya",
                    "taxonomyLabel": "ya",
                    "sourceModule": "DICTIONARY",
                }
            ],
        },
    )

    try:
        await apply_correction("draft-1", "corr-1", client_revision=4)
    except CorrectionNotAvailableError as error:
        assert error.latest_draft.id == "draft-1"
    else:
        raise AssertionError("Expected a correction conflict")
