"""Shared editor API contract models and normalization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from src.services.gec.schemas import CandidateEdit, ModuleName
from src.services.ged.schemas import ErrorCategory, ErrorSpan
from src.services.nws.schemas import Suggestion as NWSSuggestion


class CorrectionBucket(StrEnum):
    """Top-level correction buckets used by the frontend."""

    SPELLING = "spelling"
    GRAMMAR = "grammar"
    STYLE = "style"


class CorrectionStatus(StrEnum):
    """Supported correction statuses."""

    ACTIVE = "active"
    ACCEPTED = "accepted"
    IGNORED = "ignored"
    STALE = "stale"


class EditorSelection(BaseModel):
    """A selection range in the editor."""

    start: int
    end: int


class EditorFindingBase(BaseModel):
    """Shared frontend-ready analysis finding payload."""

    id: str
    category: CorrectionBucket
    bucket: CorrectionBucket
    status: CorrectionStatus = CorrectionStatus.ACTIVE
    span: EditorSelection
    title: str
    lineLabel: str
    original: str
    explanation: str
    ruleLabel: str
    taxonomyCode: str
    taxonomyLabel: str
    sourceModule: str
    confidence: float | None = None
    tokenRefs: list[int] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)


class EditorCorrection(EditorFindingBase):
    """Actionable finding with a suggested replacement."""

    kind: Literal["correction"] = "correction"
    actionable: Literal[True] = True
    replacement: str


class EditorDetection(EditorFindingBase):
    """Detection-only GED finding with no replacement."""

    kind: Literal["detection"] = "detection"
    actionable: Literal[False] = False
    replacement: None = None


EditorFinding = Annotated[
    EditorCorrection | EditorDetection, Field(discriminator="kind")
]


class DraftSummaryResponse(BaseModel):
    """Draft summary returned by the list endpoint."""

    id: str
    title: str
    stageLabel: str
    updatedAt: str


class DraftResponse(BaseModel):
    """Full draft payload returned by editor endpoints."""

    id: str
    title: str
    body: str
    stageLabel: str
    updatedAt: str
    savedAt: str
    revision: int
    formatting: dict = Field(default_factory=dict)
    corrections: list[EditorFinding] = Field(default_factory=list)


class DraftUpdateResponse(BaseModel):
    """Draft update response."""

    draft: DraftResponse
    persistedRevision: int
    savedAt: str


class AnalyzeRequest(BaseModel):
    """Analyze request."""

    title: str | None = None
    body: str | None = None
    selection: EditorSelection | None = None
    caret: int | None = None
    clientRevision: int | None = None
    categories: list[CorrectionBucket] | None = None


class AnalyzeResponse(BaseModel):
    """Analyze response."""

    analysisRevision: int
    corrections: list[EditorFinding] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)


class DraftCreateRequest(BaseModel):
    """Draft creation request."""

    title: str | None = None
    body: str | None = None


class DraftUpdateRequest(BaseModel):
    """Draft update request."""

    title: str | None = None
    body: str | None = None
    formatting: dict | None = None
    clientRevision: int | None = None


class CorrectionActionRequest(BaseModel):
    """Accept/ignore correction request."""

    body: str | None = None
    clientRevision: int | None = None


class AcceptCorrectionResponse(BaseModel):
    """Accept correction response."""

    draftBody: str
    persistedRevision: int
    corrections: list[EditorFinding] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)


class IgnoreCorrectionResponse(BaseModel):
    """Ignore correction response."""

    correctionId: str
    status: CorrectionStatus = CorrectionStatus.IGNORED
    corrections: list[EditorFinding] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)


class SuggestionMode(StrEnum):
    """Frontend suggestion modes."""

    WORD = "word"
    SENTENCE = "sentence"


class SuggestionRequest(BaseModel):
    """Suggestion request."""

    body: str
    selection: EditorSelection
    caret: int
    clientRevision: int | None = None
    mode: SuggestionMode
    limit: int = 3


class SuggestionItem(BaseModel):
    """Normalized suggestion item."""

    id: str
    label: str
    insertText: str
    displayText: str
    kind: SuggestionMode


class SuggestionResponse(BaseModel):
    """Suggestion response."""

    suggestionSessionId: str
    mode: SuggestionMode
    replaceRange: EditorSelection
    suggestions: list[SuggestionItem] = Field(default_factory=list)


class TashkeelRequest(BaseModel):
    """Tashkeel request."""

    body: str
    selection: EditorSelection
    clientRevision: int | None = None


class TashkeelResponse(BaseModel):
    """Tashkeel response."""

    draftBody: str
    replaceRange: EditorSelection
    persistedRevision: int


class RuleCategory(StrEnum):
    """Rule categories exposed to the frontend rules browser."""

    SYNTAX = "syntax"
    ORTHOGRAPHY = "orthography"
    SEMANTICS = "semantics"
    PUNCTUATION = "punctuation"
    MORPHOLOGY = "morphology"
    MERGE = "merge"
    SPLIT = "split"


class GrammarRuleResponse(BaseModel):
    """Frontend-ready grammar rule catalog item."""

    id: str
    category: RuleCategory
    subtype: str
    tier: str
    title: str
    explanation: str
    incorrect: str = ""
    correct: str = ""
    note: str = ""


class RuleCategoryOptionResponse(BaseModel):
    """Rule category filter option."""

    value: Literal["all"] | RuleCategory
    label: str


class RevisionConflictPayload(BaseModel):
    """Payload returned with a 409 editor revision conflict."""

    latestDraft: DraftResponse


@dataclass(frozen=True)
class TaxonomyInfo:
    """Detailed taxonomy metadata for a correction."""

    bucket: CorrectionBucket
    code: str
    label: str
    source_module: str
    title: str
    rule_label: str


def summarize_draft(draft) -> DraftSummaryResponse:
    """Convert a draft document into a summary response."""
    return DraftSummaryResponse(
        id=draft.id,
        title=draft.title or "",
        stageLabel=draft.stageLabel or "",
        updatedAt=draft.updatedAt or "",
    )


def draft_to_response(draft) -> DraftResponse:
    """Convert a draft document into the full API response."""
    normalized_corrections = [
        normalize_stored_correction(draft.body or "", correction)
        for correction in draft.corrections
    ]
    return DraftResponse(
        id=draft.id,
        title=draft.title or "",
        body=draft.body or "",
        stageLabel=draft.stageLabel or "",
        updatedAt=draft.updatedAt or "",
        savedAt=draft.savedAt or "",
        revision=draft.revision,
        formatting=draft.formatting or {"strong": [], "emphasis": [], "lines": {}},
        corrections=[
            validate_editor_finding(correction) for correction in normalized_corrections
        ],
    )


def get_correction_counts(corrections: list[dict]) -> dict[str, int]:
    """Compute correction bucket counts in the frontend format."""
    counts = {
        "all": 0,
        CorrectionBucket.SPELLING.value: 0,
        CorrectionBucket.GRAMMAR.value: 0,
        CorrectionBucket.STYLE.value: 0,
    }
    for correction in corrections:
        correction = normalize_stored_correction("", correction)
        if correction.get("status") in {
            CorrectionStatus.ACCEPTED.value,
            CorrectionStatus.IGNORED.value,
        }:
            continue
        bucket = correction.get("bucket") or correction.get("category")
        if bucket in counts:
            counts[bucket] += 1
            counts["all"] += 1
    return counts


def normalize_selection(selection: EditorSelection | dict[str, int]) -> EditorSelection:
    """Return a normalized start/end selection."""
    if isinstance(selection, dict):
        start = min(selection.get("start", 0), selection.get("end", 0))
        end = max(selection.get("start", 0), selection.get("end", 0))
    else:
        start = min(selection.start, selection.end)
        end = max(selection.start, selection.end)
    return EditorSelection(start=max(0, start), end=max(0, end))


def replace_text_range(body: str, selection: EditorSelection, replacement: str) -> str:
    """Replace a text range in the editor body."""
    normalized = normalize_selection(selection)
    return body[: normalized.start] + replacement + body[normalized.end :]


def resolve_corrections(
    previous_body: str, next_body: str, corrections: list[dict]
) -> list[dict]:
    """Shift or stale active corrections after a body edit."""
    prefix = 0
    shared_length = min(len(previous_body), len(next_body))
    while prefix < shared_length and previous_body[prefix] == next_body[prefix]:
        prefix += 1

    suffix = 0
    while (
        suffix < len(previous_body) - prefix
        and suffix < len(next_body) - prefix
        and previous_body[len(previous_body) - suffix - 1]
        == next_body[len(next_body) - suffix - 1]
    ):
        suffix += 1

    previous_end = len(previous_body) - suffix
    next_end = len(next_body) - suffix
    delta = next_end - previous_end

    next_corrections: list[dict] = []
    for correction in corrections:
        if correction.get("status") != CorrectionStatus.ACTIVE.value:
            next_corrections.append(correction)
            continue

        span = correction.get("span", {})
        start = span.get("start", 0)
        end = span.get("end", 0)
        next_span = {"start": start, "end": end}

        if start >= previous_end:
            next_span = {"start": start + delta, "end": end + delta}
        elif end > prefix:
            next_corrections.append(
                {
                    **correction,
                    "status": CorrectionStatus.STALE.value,
                }
            )
            continue

        if next_body[next_span["start"] : next_span["end"]] != correction.get(
            "original", ""
        ):
            next_corrections.append(
                {
                    **correction,
                    "span": next_span,
                    "status": CorrectionStatus.STALE.value,
                }
            )
            continue

        next_corrections.append({**correction, "span": next_span})
    return next_corrections


def get_line_label(body: str, span: EditorSelection) -> str:
    """Return a user-facing line label for a correction."""
    line_number = body[: span.start].count("\n") + 1
    return f"السطر {line_number}"


def normalize_stored_correction(body: str, correction: dict) -> dict:
    """Backfill legacy correction documents to the current editor contract."""
    span = normalize_selection(correction.get("span", {"start": 0, "end": 0}))
    category = correction.get("bucket") or correction.get("category") or "style"
    if category not in {
        CorrectionBucket.SPELLING.value,
        CorrectionBucket.GRAMMAR.value,
        CorrectionBucket.STYLE.value,
    }:
        category = CorrectionBucket.STYLE.value

    replacement = correction.get("replacement")
    if replacement is None:
        replacement = correction.get("correction") or correction.get("suggestion")
    original = correction.get("original")
    if original is None and body:
        original = body[span.start : span.end]
    explanation = correction.get("explanation") or "اقتراح آلي لتحسين هذا الموضع."
    taxonomy_code = correction.get("taxonomyCode")
    if not taxonomy_code:
        taxonomy_code = {
            CorrectionBucket.SPELLING.value: "legacy:spelling",
            CorrectionBucket.GRAMMAR.value: "legacy:grammar",
            CorrectionBucket.STYLE.value: "legacy:style",
        }[category]
    taxonomy_label = correction.get("taxonomyLabel") or taxonomy_code.split(":", 1)[-1]
    title = (
        correction.get("title")
        or {
            CorrectionBucket.SPELLING.value: "تصحيح إملائي",
            CorrectionBucket.GRAMMAR.value: "تصحيح نحوي",
            CorrectionBucket.STYLE.value: "تحسين أسلوبي",
        }[category]
    )
    rule_label = (
        correction.get("ruleLabel") or correction.get("subtype") or "بيانات قديمة"
    )
    kind = correction.get("kind")
    actionable = correction.get("actionable")
    is_detection = kind == "detection" or actionable is False

    if is_detection:
        title = (
            correction.get("title")
            or {
                CorrectionBucket.SPELLING.value: "رصد إملائي",
                CorrectionBucket.GRAMMAR.value: "رصد نحوي",
                CorrectionBucket.STYLE.value: "رصد أسلوبي",
            }[category]
        )

    return {
        "id": correction.get("id", ""),
        "kind": "detection" if is_detection else "correction",
        "actionable": False if is_detection else True,
        "category": category,
        "bucket": category,
        "status": correction.get("status", CorrectionStatus.ACTIVE.value),
        "span": span.model_dump(),
        "title": title,
        "lineLabel": correction.get("lineLabel") or get_line_label(body, span),
        "original": original or "",
        "replacement": None if is_detection else (replacement or ""),
        "explanation": explanation,
        "ruleLabel": rule_label,
        "taxonomyCode": taxonomy_code,
        "taxonomyLabel": taxonomy_label,
        "sourceModule": correction.get("sourceModule")
        or correction.get("category")
        or "legacy",
        "confidence": correction.get("confidence") or correction.get("edit_confidence"),
        "tokenRefs": correction.get("tokenRefs") or correction.get("token_refs") or [],
        "alternatives": correction.get("alternatives") or [],
    }


def taxonomy_from_error(
    module_name: ModuleName, error_span: ErrorSpan | None
) -> TaxonomyInfo:
    """Map GED/GEC metadata into frontend taxonomy."""
    if error_span is not None:
        category = error_span.category
        if category in {ErrorCategory.ORTHOGRAPHY, ErrorCategory.PUNCTUATION}:
            bucket = CorrectionBucket.SPELLING
        elif category in {ErrorCategory.MORPHOLOGY, ErrorCategory.SYNTAX}:
            bucket = CorrectionBucket.GRAMMAR
        else:
            bucket = CorrectionBucket.STYLE
        code = f"{category.value}:{error_span.subtype}"
        label = error_span.subtype.replace("_", " ")
        title = {
            CorrectionBucket.SPELLING: "تصحيح إملائي",
            CorrectionBucket.GRAMMAR: "تصحيح نحوي",
            CorrectionBucket.STYLE: "تحسين أسلوبي",
        }[bucket]
        return TaxonomyInfo(
            bucket=bucket,
            code=code,
            label=label,
            source_module=module_name.value,
            title=title,
            rule_label=f"{category.value} / {error_span.subtype}",
        )

    if module_name == ModuleName.DICTIONARY:
        return TaxonomyInfo(
            bucket=CorrectionBucket.SPELLING,
            code="DICTIONARY:lexical",
            label="lexical",
            source_module=module_name.value,
            title="تصحيح إملائي",
            rule_label="اقتراح القاموس",
        )
    if module_name == ModuleName.ONTOLOGY:
        return TaxonomyInfo(
            bucket=CorrectionBucket.GRAMMAR,
            code="ONTOLOGY:relation",
            label="relation",
            source_module=module_name.value,
            title="تصحيح نحوي",
            rule_label="اقتراح العلاقات",
        )
    return TaxonomyInfo(
        bucket=CorrectionBucket.STYLE,
        code=f"{module_name.value}:general",
        label="general",
        source_module=module_name.value,
        title="تحسين أسلوبي",
        rule_label="اقتراح عام",
    )


def normalize_candidate_edit(
    correction_id: str,
    body: str,
    candidate: CandidateEdit,
    module_name: ModuleName,
    error_span: ErrorSpan | None = None,
) -> dict:
    """Convert a candidate edit into a frontend-ready correction dict."""
    span = EditorSelection(start=candidate.span[0], end=candidate.span[1])
    taxonomy = taxonomy_from_error(module_name, error_span)
    original = body[span.start : span.end]
    replacement = candidate.correction
    explanation = candidate.explanation or "اقتراح آلي لتحسين هذا الموضع."
    taxonomy_label = taxonomy.label.replace("_", " ")

    return EditorCorrection(
        id=correction_id,
        category=taxonomy.bucket,
        bucket=taxonomy.bucket,
        status=CorrectionStatus.ACTIVE,
        span=span,
        title=taxonomy.title,
        lineLabel=get_line_label(body, span),
        original=original,
        replacement=replacement,
        explanation=explanation,
        ruleLabel=taxonomy.rule_label,
        taxonomyCode=taxonomy.code,
        taxonomyLabel=taxonomy_label,
        sourceModule=taxonomy.source_module,
        confidence=candidate.edit_confidence,
        tokenRefs=list(candidate.token_refs),
        alternatives=list(candidate.alternatives or []),
    ).model_dump(mode="json")


def normalize_error_detection(
    detection_id: str,
    body: str,
    error_span: ErrorSpan,
) -> dict:
    """Convert a pure GED detection into a frontend-ready finding dict."""
    span = EditorSelection(start=error_span.span[0], end=error_span.span[1])
    taxonomy = taxonomy_from_error(ModuleName.TAG, error_span)
    taxonomy_label = taxonomy.label.replace("_", " ")
    sources = ", ".join(source.value for source in error_span.sources) or "ged"

    title = {
        CorrectionBucket.SPELLING: "رصد إملائي",
        CorrectionBucket.GRAMMAR: "رصد نحوي",
        CorrectionBucket.STYLE: "رصد أسلوبي",
    }[taxonomy.bucket]

    return EditorDetection(
        id=detection_id,
        category=taxonomy.bucket,
        bucket=taxonomy.bucket,
        status=CorrectionStatus.ACTIVE,
        span=span,
        title=title,
        lineLabel=get_line_label(body, span),
        original=body[span.start : span.end],
        explanation=error_span.explanation_text
        or "تم رصد هذا الموضع دون اقتراح تصحيح مباشر.",
        ruleLabel=taxonomy.rule_label,
        taxonomyCode=taxonomy.code,
        taxonomyLabel=taxonomy_label,
        sourceModule=sources,
        confidence=error_span.confidence,
        tokenRefs=list(error_span.token_refs),
        alternatives=[],
    ).model_dump(mode="json")


def validate_editor_finding(finding: dict) -> EditorFinding:
    """Validate either correction or detection payload."""
    kind = finding.get("kind", "correction")
    if kind == "detection":
        return EditorDetection.model_validate(finding)
    return EditorCorrection.model_validate(finding)


def normalize_nws_suggestion(
    suggestion: NWSSuggestion,
    index: int,
    mode: SuggestionMode,
) -> SuggestionItem:
    """Convert an NWS suggestion into the editor suggestion contract."""
    return SuggestionItem(
        id=f"{mode.value}-{index}",
        label=suggestion.word,
        displayText=suggestion.word,
        insertText=suggestion.word,
        kind=mode,
    )


def map_suggestion_mode(mode: SuggestionMode) -> Literal["WAC", "NWP"]:
    """Map frontend suggestion modes to backend NWS modes."""
    return "WAC" if mode == SuggestionMode.WORD else "NWP"
