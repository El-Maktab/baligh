"""GED evaluation runner."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from loguru import logger

from src.runtime_config import load_runtime_config
from src.services.ged.detectors import BaseDetector
from src.services.ged.detectors.ml.artifact import read_manifest
from src.services.ged.evaluation.datasets import (
    DATASETS,
    NO_ERROR,
    UNKNOWN,
    DatasetSpec,
    GoldSentence,
    read_dataset,
)
from src.services.ged.evaluation.metrics import calculate_metrics, project_spans
from src.services.ged.evaluation.models import (
    DatasetReport,
    DatasetStats,
    EvaluationConfig,
    EvaluationReport,
    MetricReport,
)
from src.services.ged.evaluation.policy import (
    filter_evaluable_spans,
    fuse_evaluation_spans,
)
from src.services.ged.fusion import resolve_overlaps
from src.services.ged.schemas import ErrorCategory, ErrorSpan
from src.services.preprocessing import (
    PreprocessingInput,
    PreprocessingOutput,
    preprocess,
)

FUSED = "fused"
Preprocessor = Callable[[PreprocessingInput], PreprocessingOutput]


class EvaluationError(RuntimeError):
    """Raised when an evaluation cannot produce results."""


def evaluate(config: EvaluationConfig) -> EvaluationReport:
    """Run eval and report a json report."""
    unknown = sorted(set(config.datasets) - DATASETS.keys())
    if unknown:
        raise EvaluationError(f"Unknown datasets: {', '.join(unknown)}")

    try:
        # NOTE: those are here cause these imports do some parts of the GED functinality
        from src.services.ged.detectors import (
            LexiconDetector,
            MLDetector,
            RuleBasedDetector,
        )

        detectors: list[BaseDetector] = [
            RuleBasedDetector(),
            LexiconDetector(),
            MLDetector(),
        ]
        manifest = read_manifest(load_runtime_config().ged.ml.resolved_bundle_dir)
    except Exception as error:
        raise EvaluationError(f"Failed to initialize GED resources: {error}") from error

    specs = [DATASETS[name] for name in config.datasets]
    return _run(
        config,
        specs,
        detectors,
        preprocess,
        manifest["artifact_version"],
    )


def _run(
    config: EvaluationConfig,
    specs: Sequence[DatasetSpec],
    detectors: Sequence[BaseDetector],
    preprocessor: Preprocessor,
    model_version: str,
) -> EvaluationReport:
    system_names = tuple(detector.name for detector in detectors) + (FUSED,)
    aggregate_gold: list[str] = []
    aggregate_predictions: dict[str, list[set[str]]] = {
        name: [] for name in system_names
    }
    dataset_reports: dict[str, DatasetReport] = {}
    ignored_categories = frozenset(config.policy.ignored_score_categories)
    excluded_rule_subtypes = frozenset(config.policy.excluded_rule_subtypes)
    allowed_rule_subtypes = frozenset(config.policy.allowed_fusion_rule_subtypes)
    try:
        excluded_rule_categories = frozenset(
            ErrorCategory(category)
            for category in config.policy.excluded_fusion_rule_categories
        )
    except ValueError as error:
        raise EvaluationError(f"Invalid fusion policy category: {error}") from error

    for spec in specs:
        sentences = read_dataset(spec, config.limit)
        logger.info("Evaluating {} ({} sentences).", spec.name, len(sentences))
        gold, predictions, discarded_sentences, discarded_tokens = _evaluate_sentences(
            spec.name,
            sentences,
            detectors,
            preprocessor,
            excluded_rule_subtypes,
            allowed_rule_subtypes,
            excluded_rule_categories,
        )
        aggregate_gold.extend(gold)
        systems: dict[str, MetricReport] = {}
        for name in system_names:
            aggregate_predictions[name].extend(predictions[name])
            systems[name] = calculate_metrics(
                gold,
                predictions[name],
                ignored_categories,
            )

        stats = DatasetStats(
            sentences=len(sentences),
            evaluated_sentences=len(sentences) - discarded_sentences,
            discarded_sentences=discarded_sentences,
            tokens=len(gold),
            errors=sum(label != NO_ERROR for label in gold),
            unknown_errors=sum(label == UNKNOWN for label in gold),
            discarded_tokens=discarded_tokens,
        )
        dataset_reports[spec.name] = DatasetReport(
            sha256=spec.sha256,
            stats=stats,
            systems=systems,
        )
        if discarded_sentences:
            logger.warning(
                "{} sentences ({} tokens) were discarded in {} due to "
                "preprocessing/tokenization mismatch.",
                discarded_sentences,
                discarded_tokens,
                spec.name,
            )
        _log_metrics(spec.name, systems)

    aggregate = {
        name: calculate_metrics(aggregate_gold, predictions, ignored_categories)
        for name, predictions in aggregate_predictions.items()
    }
    _log_metrics("aggregate", aggregate)
    report = EvaluationReport(
        model_artifact_version=model_version,
        detector_names=system_names,
        datasets=dataset_reports,
        aggregate=aggregate,
        metric_definitions={
            "binary": "Any non-UC gold label versus any predicted GED category.",
            "categories": (
                "One-vs-rest token metrics; gold UNK tokens are excluded because "
                "their category is unspecified."
            ),
            "category_macro": "Unweighted mean over categories with gold support.",
            "false_positives_per_1000": "Binary false positives / tokens * 1000.",
            "fusion": (
                "ML baseline plus non-overlapping or confirming lexicon and "
                "allowlisted rule spans; rules never override ML."
            ),
            "ignored_score_categories": (
                "Predictions in categories absent from corpus annotation are "
                "visible in category diagnostics but excluded from primary scores."
            ),
        },
        config={
            "datasets": list(config.datasets),
            "limit": config.limit,
            "policy": config.policy.model_dump(mode="json"),
        },
    )
    _write_report(config.output_path, report)
    return report


def _evaluate_sentences(
    dataset_name: str,
    sentences: Sequence[GoldSentence],
    detectors: Sequence[BaseDetector],
    preprocessor: Preprocessor,
    excluded_rule_subtypes: frozenset[str],
    allowed_rule_subtypes: frozenset[str],
    excluded_rule_categories: frozenset[ErrorCategory],
) -> tuple[list[str], dict[str, list[set[str]]], int, int]:
    """Run detectors over sentences that survive preprocessing/tokenization checks."""
    names = tuple(detector.name for detector in detectors) + (FUSED,)
    predictions: dict[str, list[set[str]]] = {name: [] for name in names}
    gold: list[str] = []
    discarded_sentences = 0
    discarded_tokens = 0

    for sentence_number, sentence in enumerate(sentences, start=1):
        text = " ".join(sentence.tokens) + " "
        try:
            processed = preprocessor(PreprocessingInput(text=text))
        except Exception as error:
            logger.warning(
                "{} sentence {} preprocessing failed; discarding sentence: {}",
                dataset_name,
                sentence_number,
                error,
            )
            discarded_sentences += 1
            discarded_tokens += len(sentence.tokens)
            continue

        exact = len(processed.tokens) == len(sentence.tokens) and all(
            actual.form.strip() == gold_surface
            for actual, gold_surface in zip(
                processed.tokens, sentence.tokens, strict=True
            )
        )
        if not exact:
            logger.warning(
                "{} sentence {} tokenization mismatch; discarding sentence.",
                dataset_name,
                sentence_number,
            )
            discarded_sentences += 1
            discarded_tokens += len(sentence.tokens)
            continue

        spans_by_system: dict[str, list[ErrorSpan]] = {}
        for detector in detectors:
            try:
                raw_spans = detector.detect(
                    processed.text,
                    processed.normalized_text,
                    processed.tokens,
                    processed.morph_features,
                )
                evaluable_spans = filter_evaluable_spans(
                    raw_spans, excluded_rule_subtypes
                )
                spans = resolve_overlaps(evaluable_spans)
            except Exception as error:
                raise EvaluationError(
                    f"{dataset_name} sentence {sentence_number}: detector "
                    f"{detector.name} failed: {error}"
                ) from error
            spans_by_system[detector.name] = spans
        spans_by_system[FUSED] = fuse_evaluation_spans(
            spans_by_system,
            allowed_rule_subtypes,
            excluded_rule_categories,
        )

        gold.extend(sentence.labels)
        for name, spans in spans_by_system.items():
            predictions[name].extend(project_spans(len(sentence.tokens), spans))
    return gold, predictions, discarded_sentences, discarded_tokens


def _log_metrics(name: str, systems: Mapping[str, MetricReport]) -> None:
    logger.info("{} GED results", name)
    logger.info("{:<18} {:>8} {:>8} {:>8} {:>10}", "system", "P", "R", "F1", "FP/1000")
    for system_name, report in systems.items():
        binary = report.binary
        logger.info(
            "{:<18} {:>8.3f} {:>8.3f} {:>8.3f} {:>10.2f}",
            system_name,
            binary.precision,
            binary.recall,
            binary.f1,
            binary.false_positives_per_1000,
        )


def _write_report(path: Path, report: EvaluationReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    logger.info("Wrote evaluation report to {}.", path)
