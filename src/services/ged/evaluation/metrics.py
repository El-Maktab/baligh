"""Pure GED metric calculations."""

from collections.abc import Collection, Sequence

from src.services.ged.evaluation.datasets import NO_ERROR, UNKNOWN
from src.services.ged.evaluation.models import (
    BinaryMetrics,
    CategoryMetrics,
    MetricReport,
)
from src.services.ged.schemas import ErrorCategory, ErrorSpan

SUPPORTED_CATEGORIES = tuple(category.value for category in ErrorCategory)


def project_spans(token_count: int, spans: Sequence[ErrorSpan]) -> list[set[str]]:
    """Project possibly overlapping spans onto per-token category sets."""
    predictions: list[set[str]] = [set() for _ in range(token_count)]
    for span in spans:
        for token_ref in span.token_refs:
            if token_ref < 0 or token_ref >= token_count:
                raise ValueError(
                    f"Span token reference {token_ref} is outside 0..{token_count - 1}."
                )
            predictions[token_ref].add(span.category.value)
    return predictions


def calculate_metrics(
    gold: Sequence[str],
    predictions: Sequence[Collection[str]],
    ignored_categories: Collection[str] = (),
) -> MetricReport:
    """Calculate binary and supported-category token metrics."""
    if len(gold) != len(predictions):
        raise ValueError("Gold and prediction token counts differ.")

    ignored = frozenset(ignored_categories)
    scored_indexes = [index for index, label in enumerate(gold) if label not in ignored]
    true_errors = [gold[index] != NO_ERROR for index in scored_indexes]
    predicted_errors = [
        bool(set(predictions[index]) - ignored) for index in scored_indexes
    ]
    pairs = list(zip(true_errors, predicted_errors, strict=True))
    tp = sum(want and got for want, got in pairs)
    fp = sum(not want and got for want, got in pairs)
    fn = sum(want and not got for want, got in pairs)
    tn = len(scored_indexes) - tp - fp - fn
    binary = _binary_metrics(tp, fp, fn, tn, len(scored_indexes))

    known_indexes = [
        index
        for index, label in enumerate(gold)
        if label != UNKNOWN and label not in ignored
    ]
    categories = {
        category: _category_metrics(
            gold,
            predictions,
            known_indexes,
            category,
        )
        for category in SUPPORTED_CATEGORIES
    }
    scored_category_metrics = [
        metric for category, metric in categories.items() if category not in ignored
    ]
    micro = _micro_metrics(scored_category_metrics)
    populated = [metric for metric in scored_category_metrics if metric.support > 0]
    macro = _macro_metrics(populated)
    return MetricReport(
        binary=binary,
        categories=categories,
        category_micro=micro,
        category_macro=macro,
    )


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _binary_metrics(tp: int, fp: int, fn: int, tn: int, tokens: int) -> BinaryMetrics:
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    return BinaryMetrics(
        tp=tp,
        fp=fp,
        fn=fn,
        tn=tn,
        precision=precision,
        recall=recall,
        f1=_f1(precision, recall),
        false_positives_per_1000=_ratio(fp * 1000, tokens),
    )


def _category_metrics(
    gold: Sequence[str],
    predictions: Sequence[Collection[str]],
    indexes: Sequence[int],
    category: str,
) -> CategoryMetrics:
    tp = sum(
        gold[index] == category and category in predictions[index] for index in indexes
    )
    fp = sum(
        gold[index] != category and category in predictions[index] for index in indexes
    )
    fn = sum(
        gold[index] == category and category not in predictions[index]
        for index in indexes
    )
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    return CategoryMetrics(
        tp=tp,
        fp=fp,
        fn=fn,
        precision=precision,
        recall=recall,
        f1=_f1(precision, recall),
        support=tp + fn,
    )


def _micro_metrics(metrics: Collection[CategoryMetrics]) -> CategoryMetrics:
    tp = sum(metric.tp for metric in metrics)
    fp = sum(metric.fp for metric in metrics)
    fn = sum(metric.fn for metric in metrics)
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    return CategoryMetrics(
        tp=tp,
        fp=fp,
        fn=fn,
        precision=precision,
        recall=recall,
        f1=_f1(precision, recall),
        support=sum(metric.support for metric in metrics),
    )


def _macro_metrics(metrics: Sequence[CategoryMetrics]) -> CategoryMetrics:
    if not metrics:
        return CategoryMetrics(
            tp=0, fp=0, fn=0, precision=0.0, recall=0.0, f1=0.0, support=0
        )
    return CategoryMetrics(
        tp=sum(metric.tp for metric in metrics),
        fp=sum(metric.fp for metric in metrics),
        fn=sum(metric.fn for metric in metrics),
        precision=sum(metric.precision for metric in metrics) / len(metrics),
        recall=sum(metric.recall for metric in metrics) / len(metrics),
        f1=sum(metric.f1 for metric in metrics) / len(metrics),
        support=sum(metric.support for metric in metrics),
    )
