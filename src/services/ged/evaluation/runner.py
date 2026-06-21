"""GED evaluation runner."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from loguru import logger

from src.services.ged.config import load_ged_config
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
from src.services.ged.features.subsystems.base import BaseDetector
from src.services.ged.features.subsystems.ml.artifact import read_manifest
from src.services.ged.fusion import resolve_overlaps
from src.services.ged.schemas import ErrorCategory, ErrorSpan, MorphAnalysis, Token
from src.services.preprocessing import (
    PreprocessingInput,
    PreprocessingOutput,
    preprocess,
)
from src.services.preprocessing.features.analyzer import analyze

FUSED = "fused"
Preprocessor = Callable[[PreprocessingInput], PreprocessingOutput]
MorphAnalyzer = Callable[[list[Token]], list[list[MorphAnalysis]]]


class EvaluationError(RuntimeError):
    """Raised when an evaluation cannot produce results."""


def evaluate(config: EvaluationConfig) -> EvaluationReport:
    """Run eval and report a json report."""
    unknown = sorted(set(config.datasets) - DATASETS.keys())
    if unknown:
        raise EvaluationError(f"Unknown datasets: {', '.join(unknown)}")

    try:
        # NOTE: those are here cause these imports do some parts of the GED functinality
        from src.services.ged.features.subsystems.lexicon import LexiconDetector
        from src.services.ged.features.subsystems.ml import MLDetector
        from src.services.ged.features.subsystems.rule_based import RuleBasedDetector

        detectors: list[BaseDetector] = [
            RuleBasedDetector(),
            LexiconDetector(),
            MLDetector(),
        ]
        manifest = read_manifest(load_ged_config().ml.resolved_bundle_dir)
    except Exception as error:
        raise EvaluationError(f"Failed to initialize GED resources: {error}") from error

    specs = [DATASETS[name] for name in config.datasets]
    return _run(
        config,
        specs,
        detectors,
        preprocess,
        analyze,
        manifest["artifact_version"],
    )


def _run(
    config: EvaluationConfig,
    specs: Sequence[DatasetSpec],
    detectors: Sequence[BaseDetector],
    preprocessor: Preprocessor,
    morph_analyzer: MorphAnalyzer,
    model_version: str,
) -> EvaluationReport:
    system_names = tuple(detector.name for detector in detectors) + (FUSED,)
    aggregate_gold: list[str] = []
    aggregate_predictions: dict[str, list[set[str]]] = {
        name: [] for name in system_names
    }
    aggregate_fallback_mask: list[bool] = []
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
        gold, predictions, mismatch_count, fallback_mask = _evaluate_sentences(
            spec.name,
            sentences,
            detectors,
            preprocessor,
            morph_analyzer,
            excluded_rule_subtypes,
            allowed_rule_subtypes,
            excluded_rule_categories,
        )
        aggregate_gold.extend(gold)
        aggregate_fallback_mask.extend(fallback_mask)
        systems: dict[str, MetricReport] = {}
        for name in system_names:
            aggregate_predictions[name].extend(predictions[name])
            systems[name] = calculate_metrics(
                gold,
                predictions[name],
                ignored_categories,
            )

        strata = _stratified_metrics(
            gold,
            predictions,
            fallback_mask,
            ignored_categories,
        )

        stats = DatasetStats(
            sentences=len(sentences),
            tokens=len(gold),
            errors=sum(label != NO_ERROR for label in gold),
            unknown_errors=sum(label == UNKNOWN for label in gold),
            preprocessing_fallback_tokens=mismatch_count,
        )
        dataset_reports[spec.name] = DatasetReport(
            sha256=spec.sha256,
            stats=stats,
            systems=systems,
            preprocessing_strata=strata,
        )
        if mismatch_count:
            logger.warning(
                "{} gold tokens required preprocessing fallback in {}.",
                mismatch_count,
                spec.name,
            )
        _log_metrics(spec.name, systems)

    aggregate = {
        name: calculate_metrics(aggregate_gold, predictions, ignored_categories)
        for name, predictions in aggregate_predictions.items()
    }
    aggregate_strata = _stratified_metrics(
        aggregate_gold,
        aggregate_predictions,
        aggregate_fallback_mask,
        ignored_categories,
    )
    _log_metrics("aggregate", aggregate)
    for stratum_name, systems in aggregate_strata.items():
        _log_metrics(f"aggregate/{stratum_name}", systems)
    report = EvaluationReport(
        model_artifact_version=model_version,
        detector_names=system_names,
        datasets=dataset_reports,
        aggregate=aggregate,
        aggregate_preprocessing_strata=aggregate_strata,
        metric_definitions={
            "binary": "Any non-UC gold label versus any predicted GED category.",
            "categories": (
                "One-vs-rest token metrics; gold UNK tokens are excluded because "
                "their category is unspecified."
            ),
            "category_macro": "Unweighted mean over categories with gold support.",
            "false_positives_per_1000": "Binary false positives / tokens * 1000.",
            "preprocessing_fallback_tokens": (
                "Gold tokens reanalyzed directly because production preprocessing "
                "changed token surfaces, boundaries, or failed."
            ),
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
    morph_analyzer: MorphAnalyzer,
    excluded_rule_subtypes: frozenset[str],
    allowed_rule_subtypes: frozenset[str],
    excluded_rule_categories: frozenset[ErrorCategory],
) -> tuple[list[str], dict[str, list[set[str]]], int, list[bool]]:
    names = tuple(detector.name for detector in detectors) + (FUSED,)
    predictions: dict[str, list[set[str]]] = {name: [] for name in names}
    gold: list[str] = []
    fallback_mask: list[bool] = []
    mismatches = 0

    for sentence_number, sentence in enumerate(sentences, start=1):
        text = " ".join(sentence.tokens) + " "
        try:
            processed = preprocessor(PreprocessingInput(text=text))
        except Exception as error:
            logger.warning(
                "{} sentence {} preprocessing failed; using gold tokens: {}",
                dataset_name,
                sentence_number,
                error,
            )
            processed = _canonical_output(text, sentence.tokens, morph_analyzer)
            sentence_mismatches = len(sentence.tokens)
        else:
            processed, sentence_mismatches = _use_gold_tokenization(
                processed,
                sentence.tokens,
                morph_analyzer,
            )
        mismatches += sentence_mismatches

        fallback_mask.extend([sentence_mismatches > 0] * len(sentence.tokens))
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
    return gold, predictions, mismatches, fallback_mask


def _stratified_metrics(
    gold: Sequence[str],
    predictions: Mapping[str, Sequence[set[str]]],
    fallback_mask: Sequence[bool],
    ignored_categories: frozenset[str],
) -> dict[str, dict[str, MetricReport]]:
    """Compare native preprocessing with token fallback."""
    strata: dict[str, dict[str, MetricReport]] = {}
    for name, selected_value in (
        ("native_preprocessing", False),
        ("gold_fallback", True),
    ):
        indexes = [
            index
            for index, is_fallback in enumerate(fallback_mask)
            if is_fallback is selected_value
        ]
        stratum_gold = [gold[index] for index in indexes]
        strata[name] = {
            system_name: calculate_metrics(
                stratum_gold,
                [system_predictions[index] for index in indexes],
                ignored_categories,
            )
            for system_name, system_predictions in predictions.items()
        }
    return strata


def _use_gold_tokenization(
    processed: PreprocessingOutput,
    gold_tokens: Sequence[str],
    morph_analyzer: MorphAnalyzer,
) -> tuple[PreprocessingOutput, int]:
    """Replace incompatible preprocessing tokens with canonical corpus tokens."""
    exact = len(processed.tokens) == len(gold_tokens) and all(
        actual.form.strip() == gold
        for actual, gold in zip(processed.tokens, gold_tokens, strict=True)
    )
    if exact:
        return processed, 0

    canonical = _canonical_output(processed.text, gold_tokens, morph_analyzer)
    mismatch_count = len(gold_tokens)
    return canonical, mismatch_count


def _canonical_output(
    text: str,
    gold_tokens: Sequence[str],
    morph_analyzer: MorphAnalyzer,
) -> PreprocessingOutput:
    """Build detector input directly from an authoritative corpus sentence."""
    canonical_tokens: list[Token] = []
    cursor = 0
    for index, gold_surface in enumerate(gold_tokens):
        span = (cursor, cursor + len(gold_surface))
        canonical_tokens.append(
            Token(index=index, form=gold_surface, span=span, norm_span=span)
        )
        cursor += len(gold_surface) + 1
    morph_features = morph_analyzer(canonical_tokens)
    return PreprocessingOutput(
        text=text,
        normalized_text=text,
        tokens=canonical_tokens,
        morph_features=morph_features,
        current_fragment=None,
        mode="NWP",
    )


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
