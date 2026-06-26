"""Helpers for applying preprocessing-backed tashkeel to editor text."""

from __future__ import annotations

from src.api.services.editor_contract import EditorSelection, normalize_selection
from src.api.services.preprocessing import run as preprocess_run
from src.services.preprocessing.schemas import PreprocessingOutput


def resolve_tashkeel_range(body: str, selection: EditorSelection) -> EditorSelection:
    """Expand a collapsed selection to the current line."""
    normalized = normalize_selection(selection)
    if normalized.start != normalized.end:
        return normalized

    line_start = body.rfind("\n", 0, normalized.start) + 1
    next_break = body.find("\n", normalized.end)
    line_end = len(body) if next_break == -1 else next_break
    return EditorSelection(start=line_start, end=line_end)


def apply_tashkeel_with_preprocessing(
    text: str, preprocessing_output: PreprocessingOutput
) -> str:
    """Replace token surfaces with their best diacritized forms."""
    parts: list[str] = []
    cursor = 0

    for index, token in enumerate(preprocessing_output.tokens):
        start, end = token.span
        parts.append(text[cursor:start])
        analyses = (
            preprocessing_output.morph_features[index]
            if index < len(preprocessing_output.morph_features)
            else []
        )
        replacement = next(
            (analysis.diacritized for analysis in analyses if analysis.diacritized),
            None,
        )
        parts.append(replacement or text[start:end])
        cursor = end

    parts.append(text[cursor:])
    return "".join(parts)


def apply_tashkeel_to_body(
    body: str, selection: EditorSelection
) -> tuple[str, EditorSelection]:
    """Apply tashkeel to the selected range and return the updated body."""
    replace_range = resolve_tashkeel_range(body, selection)
    if replace_range.start >= replace_range.end:
        return body, replace_range

    segment = body[replace_range.start : replace_range.end]
    preprocessing_output = preprocess_run(segment)
    diacritized_segment = apply_tashkeel_with_preprocessing(
        segment, preprocessing_output
    )
    next_body = (
        body[: replace_range.start] + diacritized_segment + body[replace_range.end :]
    )
    return next_body, replace_range
