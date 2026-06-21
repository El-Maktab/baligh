"""Evaluation ploicies made to make fair eval for the modules on SOTA datasets.

Some rules are disabled because the way we test require them to be in a certain way.

Author:
  Amir Anwar
"""

from collections.abc import Sequence

from src.services.ged.fusion import resolve_overlaps
from src.services.ged.schemas import ErrorCategory, ErrorSource, ErrorSpan

RULE_SOURCE = ErrorSource.RULE_BASED


def filter_evaluable_spans(
    spans: Sequence[ErrorSpan], excluded_rule_subtypes: frozenset[str]
) -> list[ErrorSpan]:
    """Remove some rules."""
    return [
        span
        for span in spans
        if not (RULE_SOURCE in span.sources and span.subtype in excluded_rule_subtypes)
    ]


def fuse_evaluation_spans(
    spans_by_source: dict[str, list[ErrorSpan]],
    allowed_rule_subtypes: frozenset[str],
    excluded_rule_categories: frozenset[ErrorCategory],
) -> list[ErrorSpan]:
    """Custom fusion policy for eval."""
    ml_name = ErrorSource.SEQUENCE_LABELER.value
    ml_spans = spans_by_source.get(ml_name, [])
    accepted = list(ml_spans)

    for source_name, spans in spans_by_source.items():
        if source_name == ml_name:
            continue
        for span in spans:
            if RULE_SOURCE in span.sources:
                if span.category in excluded_rule_categories:
                    continue
                if span.subtype not in allowed_rule_subtypes:
                    continue
            if _supplements_or_confirms(span, ml_spans):
                accepted.append(span)
    return resolve_overlaps(accepted)


def _supplements_or_confirms(
    candidate: ErrorSpan, ml_spans: Sequence[ErrorSpan]
) -> bool:
    """Checks if a candidate confirms or sompplements ML."""
    for ml_span in ml_spans:
        overlaps = (
            candidate.span[0] < ml_span.span[1] and ml_span.span[0] < candidate.span[1]
        )
        if not overlaps:
            continue
        return candidate.span == ml_span.span and candidate.category == ml_span.category
    return True
