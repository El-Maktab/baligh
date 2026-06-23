"""Train and export the GED CRF sequence labeler."""

from __future__ import annotations

import argparse
import contextlib
import json
import platform
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
from sklearn_crfsuite import CRF
from src.services.ged.config import GED_ROOT
from src.services.ged.evaluation.datasets import LABEL_TO_CATEGORY, NO_ERROR
from src.services.ged.evaluation.metrics import calculate_metrics
from src.services.ged.features.subsystems.ml.artifact import (
    DEFAULT_THRESHOLD,
    installed_runtime_versions,
    write_bundle,
)
from src.services.ged.features.subsystems.ml.features import (
    FEATURE_SET_VERSION,
    sentence_features,
)
from src.services.preprocessing import PreprocessingInput, preprocess

FORBIDDEN_SUBSTRINGS = ("&gt;", "&lt;", ">", "<")
DATA_ROOT = GED_ROOT / "data" / "ml"
DEFAULT_MODEL_NAME = "baligh-ged-crf-surface-morph-v2"
DEFAULT_ARTIFACT_VERSION = "0.2.0"
DEFAULT_THRESHOLDS = tuple(round(step / 100, 2) for step in range(5, 95, 5))


@dataclass(frozen=True)
class RawSentence:
    """One token-label sequence from a GED corpus."""

    tokens: tuple[str, ...]
    raw_labels: tuple[str, ...]


@dataclass(frozen=True)
class PreparedSentence:
    """A training or development sentence after Baligh preprocessing."""

    features: list[dict[str, object]]
    labels: list[str]


@dataclass(frozen=True)
class PreparationStats:
    """Preparation counters for one split."""

    total_sentences: int
    kept_sentences: int
    discarded_forbidden_sentences: int
    discarded_mismatch_sentences: int
    total_tokens: int
    kept_tokens: int

    def as_dict(self) -> dict[str, int]:
        """Return JSON-friendly counters."""
        return {
            "total_sentences": self.total_sentences,
            "kept_sentences": self.kept_sentences,
            "discarded_forbidden_sentences": self.discarded_forbidden_sentences,
            "discarded_mismatch_sentences": self.discarded_mismatch_sentences,
            "total_tokens": self.total_tokens,
            "kept_tokens": self.kept_tokens,
        }


def _log(message: str) -> None:
    """Print a flush-always training log line."""
    print(message, flush=True)


def _format_seconds(seconds: float) -> str:
    """Format an elapsed time for human-readable logs."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, remaining = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)}m {remaining:.1f}s"
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours)}h {int(minutes)}m {remaining:.1f}s"


def dataset_dir(name: str) -> Path:
    """Return the local dataset directory for a training corpus."""
    path = DATA_ROOT / name / "data"
    if not path.is_dir():
        raise FileNotFoundError(f"Training dataset {name!r} is missing: {path}")
    return path


def read_labeled_sentences(path: Path) -> list[RawSentence]:
    """Read a sentence-separated token-label corpus."""
    sentences: list[RawSentence] = []
    tokens: list[str] = []
    labels: list[str] = []

    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line:
            if tokens:
                sentences.append(RawSentence(tuple(tokens), tuple(labels)))
                tokens, labels = [], []
            continue

        fields = line.split("\t")
        if len(fields) != 2:
            raise ValueError(f"{path}:{line_number}: expected TOKEN<TAB>LABEL.")
        token, label = fields
        tokens.append(token)
        labels.append(label)

    if tokens:
        sentences.append(RawSentence(tuple(tokens), tuple(labels)))
    return sentences


def _contains_forbidden_symbol(tokens: Sequence[str]) -> bool:
    return any(
        any(symbol in token for symbol in FORBIDDEN_SUBSTRINGS) for token in tokens
    )


def prepare_sentences(
    sentences: Sequence[RawSentence],
) -> tuple[list[PreparedSentence], PreparationStats]:
    """Keep only sentences that align exactly with Baligh preprocessing."""
    started_at = time.perf_counter()
    prepared: list[PreparedSentence] = []
    discarded_forbidden = 0
    discarded_mismatch = 0
    total_tokens = 0
    kept_tokens = 0

    for index, sentence in enumerate(sentences, start=1):
        if index % 250 == 0:
            _log(
                f"prepared {index}/{len(sentences)} sentences "
                f"(kept={len(prepared)}, forbidden={discarded_forbidden}, "
                f"mismatch={discarded_mismatch})",
            )
        total_tokens += len(sentence.tokens)
        if _contains_forbidden_symbol(sentence.tokens):
            discarded_forbidden += 1
            continue

        try:
            processed = preprocess(
                PreprocessingInput(text=" ".join(sentence.tokens) + " ")
            )
        except Exception:
            discarded_mismatch += 1
            continue
        exact = len(processed.tokens) == len(sentence.tokens) and all(
            actual.form.strip() == gold
            for actual, gold in zip(processed.tokens, sentence.tokens, strict=True)
        )
        if not exact:
            discarded_mismatch += 1
            continue

        labels = [LABEL_TO_CATEGORY[label] for label in sentence.raw_labels]
        prepared.append(
            PreparedSentence(
                features=sentence_features(processed.tokens, processed.morph_features),
                labels=labels,
            )
        )
        kept_tokens += len(labels)

    stats = PreparationStats(
        total_sentences=len(sentences),
        kept_sentences=len(prepared),
        discarded_forbidden_sentences=discarded_forbidden,
        discarded_mismatch_sentences=discarded_mismatch,
        total_tokens=total_tokens,
        kept_tokens=kept_tokens,
    )
    _log(
        "finished sentence preparation "
        f"({stats.kept_sentences}/{stats.total_sentences} kept, "
        f"{stats.discarded_forbidden_sentences} forbidden, "
        f"{stats.discarded_mismatch_sentences} mismatch) in "
        f"{_format_seconds(time.perf_counter() - started_at)}"
    )
    return prepared, stats


def load_split(
    dataset_names: Sequence[str], split_name: str
) -> tuple[list[PreparedSentence], dict[str, dict[str, int]]]:
    """Load and prepare a named split from one or more datasets."""
    return load_split_with_cache(dataset_names, split_name, cache_dir=None)


def load_split_with_cache(
    dataset_names: Sequence[str],
    split_name: str,
    *,
    cache_dir: Path | None,
) -> tuple[list[PreparedSentence], dict[str, dict[str, int]]]:
    """Load and prepare a named split from one or more datasets, with caching."""
    sentences: list[PreparedSentence] = []
    stats: dict[str, dict[str, int]] = {}
    for dataset_name in dataset_names:
        split_started_at = time.perf_counter()
        cache_path = None
        if cache_dir is not None:
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_path = (
                cache_dir / f"{dataset_name}_{split_name}_{FEATURE_SET_VERSION}.joblib"
            )
        if cache_path is not None and cache_path.is_file():
            try:
                prepared, prepared_stats = joblib.load(cache_path)
                _log(
                    f"loaded cached {dataset_name}/{split_name} preparation "
                    f"in {_format_seconds(time.perf_counter() - split_started_at)}"
                )
            except (EOFError, ValueError):
                cache_path.unlink(missing_ok=True)
                _log(f"rebuilding corrupted cache for {dataset_name}/{split_name}")
                raw_sentences = read_labeled_sentences(
                    dataset_dir(dataset_name) / f"{split_name}.txt"
                )
                prepared, prepared_stats = prepare_sentences(raw_sentences)
                _atomic_joblib_dump((prepared, prepared_stats), cache_path)
        else:
            _log(f"preparing {dataset_name}/{split_name} from source")
            raw_sentences = read_labeled_sentences(
                dataset_dir(dataset_name) / f"{split_name}.txt"
            )
            prepared, prepared_stats = prepare_sentences(raw_sentences)
            if cache_path is not None:
                _atomic_joblib_dump((prepared, prepared_stats), cache_path)
                _log(f"cached {dataset_name}/{split_name} preparation to {cache_path}")
        sentences.extend(prepared)
        stats[dataset_name] = prepared_stats.as_dict()
        _log(
            f"finished {dataset_name}/{split_name} with "
            f"{prepared_stats.kept_sentences} kept sentences in "
            f"{_format_seconds(time.perf_counter() - split_started_at)}"
        )
    return sentences, stats


def _atomic_joblib_dump(value: Any, path: Path) -> None:
    """Write a joblib cache file atomically."""
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with contextlib.suppress(FileNotFoundError):
        temp_path.unlink()
    joblib.dump(value, temp_path)
    temp_path.replace(path)


def to_xy(
    sentences: Sequence[PreparedSentence],
) -> tuple[list[list[dict[str, object]]], list[list[str]]]:
    """Split prepared sentences into CRF matrices and label sequences."""
    return [sentence.features for sentence in sentences], [
        sentence.labels for sentence in sentences
    ]


def _predictions_to_sets(labels: Sequence[str]) -> list[set[str]]:
    return [set() if label == NO_ERROR else {label} for label in labels]


def predict_with_threshold(
    model: CRF,
    sentences: Sequence[list[dict[str, object]]],
    threshold: float,
) -> list[list[str]]:
    """Decode with a minimum non-UC marginal threshold."""
    error_labels = tuple(label for label in model.classes_ if label != NO_ERROR)
    predictions: list[list[str]] = []
    for marginal_sentence in model.predict_marginals(sentences):
        sentence_labels: list[str] = []
        for marginals in marginal_sentence:
            label = max(error_labels, key=lambda item: marginals.get(item, 0.0))
            confidence = marginals.get(label, 0.0)
            sentence_labels.append(label if confidence >= threshold else NO_ERROR)
        predictions.append(sentence_labels)
    return predictions


def evaluate_thresholds(
    model: CRF,
    dev_x: Sequence[list[dict[str, object]]],
    dev_y: Sequence[list[str]],
    thresholds: Iterable[float],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Score threshold operating points and return the best one."""
    flat_gold = [label for sentence in dev_y for label in sentence]
    rows: list[dict[str, Any]] = []

    for threshold in thresholds:
        predicted = predict_with_threshold(model, dev_x, float(threshold))
        flat_predictions = [
            prediction
            for sentence in predicted
            for prediction in _predictions_to_sets(sentence)
        ]
        metrics = calculate_metrics(flat_gold, flat_predictions)
        mbfp = metrics.binary.false_positives_per_1000
        rows.append(
            {
                "threshold": float(threshold),
                "tp": metrics.binary.tp,
                "fp": metrics.binary.fp,
                "fn": metrics.binary.fn,
                "tn": metrics.binary.tn,
                "precision": metrics.binary.precision,
                "recall": metrics.binary.recall,
                "f1": metrics.binary.f1,
                "false_positives_per_1000_tokens": mbfp,
            }
        )

    best = max(rows, key=lambda row: (row["f1"], row["recall"], -row["fp"]))
    return rows, best


def train_model(
    train_x: Sequence[list[dict[str, object]]],
    train_y: Sequence[list[str]],
    dev_x: Sequence[list[dict[str, object]]],
    dev_y: Sequence[list[str]],
    *,
    c1_values: Sequence[float],
    c2_values: Sequence[float],
    max_iterations_values: Sequence[int],
    thresholds: Sequence[float],
) -> tuple[CRF, dict[str, Any], list[dict[str, Any]]]:
    """Run a small CRF sweep and return the best model."""
    best_model: CRF | None = None
    best_row: dict[str, Any] | None = None
    best_sweep: list[dict[str, Any]] = []

    for c1 in c1_values:
        for c2 in c2_values:
            for max_iterations in max_iterations_values:
                fit_started_at = time.perf_counter()
                _log(
                    "starting CRF fit "
                    f"(c1={c1}, c2={c2}, max_iterations={max_iterations})"
                )
                model = CRF(
                    algorithm="lbfgs",
                    c1=float(c1),
                    c2=float(c2),
                    max_iterations=int(max_iterations),
                    all_possible_transitions=True,
                )
                model.fit(train_x, train_y)
                _log(
                    "finished CRF fit "
                    f"(c1={c1}, c2={c2}, max_iterations={max_iterations}) in "
                    f"{_format_seconds(time.perf_counter() - fit_started_at)}"
                )
                threshold_started_at = time.perf_counter()
                _log("starting threshold sweep")
                sweep, row = evaluate_thresholds(model, dev_x, dev_y, thresholds)
                _log(
                    "finished threshold sweep in "
                    f"{_format_seconds(time.perf_counter() - threshold_started_at)}; "
                    f"best threshold this run={row['threshold']:.2f}, "
                    f"f1={row['f1']:.4f}, recall={row['recall']:.4f}"
                )
                row["c1"] = float(c1)
                row["c2"] = float(c2)
                row["max_iterations"] = int(max_iterations)

                if best_row is None or (
                    row["f1"],
                    row["recall"],
                    -row["fp"],
                ) > (
                    best_row["f1"],
                    best_row["recall"],
                    -best_row["fp"],
                ):
                    best_model = model
                    best_row = row
                    best_sweep = sweep

    if best_model is None or best_row is None:
        raise RuntimeError("No CRF model was trained.")
    return best_model, best_row, best_sweep


def _model_card(
    *,
    manifest: dict[str, Any],
    dataset_names: Sequence[str],
    dev_dataset_names: Sequence[str],
    best_row: dict[str, Any],
) -> str:
    title = manifest["model"]["name"].replace("-", " ").title()
    dataset_list = ", ".join(dataset_names)
    dev_list = ", ".join(dev_dataset_names)
    return f"""---
library_name: sklearn-crfsuite
language:
- ar
pipeline_tag: token-classification
tags:
- grammatical-error-detection
- crf
- arabic
- morphology
---

# {title}

This is Baligh's morphology-aware Arabic grammatical error detection CRF. It
uses Baligh preprocessing tokens plus the disambiguated morphological features
from preprocessing output, and emits the mapped labels `UC`, `OT`, `MO`, `SY`,
`PC`, `MG`, `SP`, and `UNK`.

## Selected development operating point

- Training datasets: {dataset_list}
- Development datasets: {dev_list}
- Threshold: `{best_row["threshold"]:.2f}`
- Binary error F1: `{best_row["f1"]:.6f}`
- Precision: `{best_row["precision"]:.6f}`
- Recall: `{best_row["recall"]:.6f}`
- False positives per 1,000 tokens: `{best_row["false_positives_per_1000_tokens"]:.6f}`

The threshold applies to the strongest non-`UC` marginal. The selected error
category is emitted only when that marginal clears the threshold.

## Files

- `model.joblib`: trusted sklearn-crfsuite model artifact
- `manifest.json`: model, feature, threshold, data, and dependency metadata
- `label_mapping.json`: QALB-to-Baligh mapping
- `threshold_sweep.json`: development operating-point sweep
- `smoke_test.json`: dependency-free inference probe
- `requirements.txt`: exact loading dependencies
- `SHA256SUMS`: integrity checks

## Safety and licensing

Joblib uses pickle internally. Load this model only from a trusted repository
and verify `SHA256SUMS` first. Keep the repository private until QALB-derived
model redistribution and the intended model license have been reviewed.
"""


def train_and_export(
    *,
    train_datasets: Sequence[str],
    dev_datasets: Sequence[str],
    artifact_dir: Path,
    artifact_version: str,
    model_name: str,
    c1_values: Sequence[float],
    c2_values: Sequence[float],
    max_iterations_values: Sequence[int],
    thresholds: Sequence[float],
    cache_dir: Path | None,
) -> dict[str, Any]:
    """Train the best CRF and export it as a production bundle."""
    overall_started_at = time.perf_counter()
    _log(f"starting training run with train datasets={list(train_datasets)}")
    _log(f"using dev datasets={list(dev_datasets)}")
    train_sentences, train_stats = load_split_with_cache(
        train_datasets,
        "train",
        cache_dir=cache_dir,
    )
    _log(
        f"finished train preparation with {len(train_sentences)} sentences "
        f"in {_format_seconds(time.perf_counter() - overall_started_at)}"
    )
    dev_started_at = time.perf_counter()
    dev_sentences, dev_stats = load_split_with_cache(
        dev_datasets,
        "dev",
        cache_dir=cache_dir,
    )
    _log(
        f"finished dev preparation with {len(dev_sentences)} sentences "
        f"in {_format_seconds(time.perf_counter() - dev_started_at)}"
    )
    train_x, train_y = to_xy(train_sentences)
    dev_x, dev_y = to_xy(dev_sentences)
    _log(
        f"assembled feature matrices: train={len(train_x)} sentences, "
        f"dev={len(dev_x)} sentences"
    )

    model, best_row, threshold_sweep = train_model(
        train_x,
        train_y,
        dev_x,
        dev_y,
        c1_values=c1_values,
        c2_values=c2_values,
        max_iterations_values=max_iterations_values,
        thresholds=thresholds,
    )

    smoke_input = preprocess(PreprocessingInput(text="هاذا كتاب جميل . "))
    _log("running smoke prediction")
    smoke_predictions = predict_with_threshold(
        model,
        [sentence_features(smoke_input.tokens, smoke_input.morph_features)],
        float(best_row["threshold"]),
    )[0]

    manifest = {
        "artifact_schema_version": 1,
        "artifact_version": artifact_version,
        "model": {
            "name": model_name,
            "family": "sklearn_crfsuite.CRF",
            "algorithm": "lbfgs",
            "c1": best_row["c1"],
            "c2": best_row["c2"],
            "max_iterations": best_row["max_iterations"],
            "num_attributes": len(getattr(model, "state_features_", {}))
            + len(getattr(model, "transition_features_", {})),
        },
        "features": {
            "version": FEATURE_SET_VERSION,
            "morphology_required": True,
            "tokenization": "Baligh preprocessing tokens with disambiguated morphology",
        },
        "labels": {
            "no_error": NO_ERROR,
            "model_classes": list(model.classes_),
            "mapping_file": "label_mapping.json",
        },
        "inference": {
            "error_threshold": best_row["threshold"],
        },
        "development_metrics": best_row,
        "training": {
            "train_datasets": list(train_datasets),
            "dev_datasets": list(dev_datasets),
            "train_preparation": train_stats,
            "dev_preparation": dev_stats,
        },
        "runtime": {
            "python": platform.python_version(),
            "packages": installed_runtime_versions(),
        },
        "smoke_test": {
            "tokens": [token.form for token in smoke_input.tokens],
            "predictions": smoke_predictions,
        },
    }
    if (artifact_dir / "model.joblib").exists():
        (artifact_dir / "model.joblib").unlink()
    readme = _model_card(
        manifest=manifest,
        dataset_names=train_datasets,
        dev_dataset_names=dev_datasets,
        best_row=best_row,
    )
    write_bundle(
        artifact_dir,
        model=model,
        manifest=manifest,
        label_mapping=LABEL_TO_CATEGORY,
        threshold_sweep=threshold_sweep,
        smoke_test=manifest["smoke_test"],
        readme=readme,
    )
    _log(
        f"wrote model bundle to {artifact_dir} in "
        f"{_format_seconds(time.perf_counter() - overall_started_at)}"
    )
    return manifest


def _parse_csv_floats(raw: str) -> list[float]:
    return [float(item) for item in raw.split(",") if item]


def _parse_csv_ints(raw: str) -> list[int]:
    return [int(item) for item in raw.split(",") if item]


def main() -> None:
    """Train and export the morphology-aware GED CRF."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--train-datasets",
        nargs="+",
        default=["qalb14", "qalb15"],
    )
    parser.add_argument(
        "--dev-datasets",
        nargs="+",
        default=["qalb14", "qalb15"],
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=Path("artifacts/ged/ml/crf-surface-morph-v2/v0.2.0"),
    )
    parser.add_argument(
        "--artifact-version",
        default=DEFAULT_ARTIFACT_VERSION,
    )
    parser.add_argument(
        "--model-name",
        default=DEFAULT_MODEL_NAME,
    )
    parser.add_argument(
        "--c1-grid",
        default="0.05,0.1,0.2",
    )
    parser.add_argument(
        "--c2-grid",
        default="0.05,0.1,0.2",
    )
    parser.add_argument(
        "--max-iterations-grid",
        default="100,150",
    )
    parser.add_argument(
        "--thresholds",
        default=",".join(str(value) for value in DEFAULT_THRESHOLDS),
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("artifacts/ged/ml/.cache"),
    )
    args = parser.parse_args()

    manifest = train_and_export(
        train_datasets=args.train_datasets,
        dev_datasets=args.dev_datasets,
        artifact_dir=args.artifact_dir,
        artifact_version=args.artifact_version,
        model_name=args.model_name,
        c1_values=_parse_csv_floats(args.c1_grid),
        c2_values=_parse_csv_floats(args.c2_grid),
        max_iterations_values=_parse_csv_ints(args.max_iterations_grid),
        thresholds=_parse_csv_floats(args.thresholds) or [DEFAULT_THRESHOLD],
        cache_dir=args.cache_dir,
    )
    print(json.dumps(manifest["development_metrics"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
