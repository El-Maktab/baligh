"""Fusion model handles conflict resolution and merging of GED.

Authors:
  Amir Anwar
"""

from src.services.ged.schemas import ErrorSource, ErrorSpan, ProvenanceTier

# ###########################################################################
# Internal helpers
# ###########################################################################

_TIER_PRIORITY: dict[ProvenanceTier, int] = {
    ProvenanceTier.TIER_1_RULE_DERIVED: 1,
    ProvenanceTier.TIER_2_RULE_SUPPORTED: 2,
    ProvenanceTier.TIER_3_STATISTICAL: 3,
}


def _tier_rank(span: ErrorSpan) -> float:
    """Lower rank -> higher priority, unmapped = inf."""
    return _TIER_PRIORITY.get(span.provenance_tier, float("inf"))


def _overlaps(a: ErrorSpan, b: ErrorSpan) -> bool:
    return a.span[0] < b.span[1] and b.span[0] < a.span[1]


def _is_contained_in(inner: ErrorSpan, outer: ErrorSpan) -> bool:
    return outer.span[0] <= inner.span[0] and inner.span[1] <= outer.span[1]


def _merge_sources(a: ErrorSpan, b: ErrorSpan) -> list[ErrorSource]:
    """Union of sources from both spans, preserving insertion order."""
    return list(dict.fromkeys(list(a.sources) + list(b.sources)))


def _resolve_conflict(prev: ErrorSpan, curr: ErrorSpan) -> list[ErrorSpan]:
    """Applies conflict resolution to a pair."""
    if not _overlaps(prev, curr):
        return [prev, curr]

    prev_tier = _tier_rank(prev)
    curr_tier = _tier_rank(curr)

    if prev.span == curr.span:
        if prev.category == curr.category:
            winner, loser = (
                (prev, curr) if prev.confidence >= curr.confidence else (curr, prev)
            )
            return [
                winner.model_copy(update={"sources": _merge_sources(winner, loser)})
            ]

        return [curr] if curr.confidence > prev.confidence else [prev]

    if _is_contained_in(curr, prev):
        if curr.category != prev.category:
            return [prev, curr]
        return [curr] if curr.confidence > prev.confidence else [prev]

    tier_3_rank = _TIER_PRIORITY[ProvenanceTier.TIER_3_STATISTICAL]

    if prev_tier < curr_tier and curr_tier == tier_3_rank:
        return [prev]  # Suppress incoming tier_3

    if curr_tier < prev_tier and prev_tier == tier_3_rank:
        return [curr]  # Replace previous tier_3 with incoming higher-tier

    if prev.category == curr.category and prev_tier == curr_tier:
        # Widen into a merged span
        merged = prev.model_copy(
            update={
                "span": (
                    min(prev.span[0], curr.span[0]),
                    max(prev.span[1], curr.span[1]),
                ),
                "token_refs": sorted(set(prev.token_refs) | set(curr.token_refs)),
                "confidence": max(prev.confidence, curr.confidence),
                "sources": _merge_sources(prev, curr),
            }
        )
        return [merged]

    return [curr] if curr.confidence > prev.confidence else [prev]


def _normalize_eligibility(spans: list[ErrorSpan]) -> list[ErrorSpan]:
    """Ensures that all tier 3 spans are marked as ineligible for explanations."""
    result = []
    for span in spans:
        if span.provenance_tier == ProvenanceTier.TIER_3_STATISTICAL:
            result.append(
                span.model_copy(
                    update={"explanation_eligible": False, "explanation_text": None}
                )
            )
        elif not span.explanation_eligible:
            result.append(span.model_copy(update={"explanation_eligible": True}))
        else:
            result.append(span)
    return result


# ###########################################################################
# Public API
# ###########################################################################


def resolve_overlaps(errors: list[ErrorSpan]) -> list[ErrorSpan]:
    """Resolve overlapping errors.

    Args:
        errors: List of errors

    Returns:
        A list of errors with overlaps resolved.
    """
    if not errors:
        return []

    # Pass 1 : Sort
    sorted_errors = sorted(errors, key=lambda e: (e.span[0], -e.span[1], -e.confidence))

    # Pass 2 : Sweep with decision table
    accepted: list[ErrorSpan] = [sorted_errors[0]]

    for current in sorted_errors[1:]:
        previous = accepted.pop()

        # _resolve_conflict returns 1 or 2 items
        accepted.extend(_resolve_conflict(previous, current))

    # Pass 3 : Eligibility
    return _normalize_eligibility(accepted)
