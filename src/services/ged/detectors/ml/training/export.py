"""Train and export the GED CRF as a production artifact bundle."""

from __future__ import annotations

import platform
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from src.services.ged.detectors.ml.artifact import (
    MODEL_NAME,
    installed_runtime_versions,
    write_bundle,
)
from src.services.ged.detectors.ml.features import (
    FEATURE_SET_VERSION,
    sentence_features,
)
from src.services.ged.detectors.ml.labels import NO_ERROR
from src.services.ged.detectors.ml.training.experiment import (
    predict_with_threshold,
    train_model,
)
from src.services.ged.detectors.ml.training.logging import format_seconds, log
from src.services.ged.detectors.ml.training.preparation import (
    load_split_with_cache,
    to_xy,
)
from src.services.ged.evaluation.datasets import LABEL_TO_CATEGORY
from src.services.preprocessing import PreprocessingInput, preprocess


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
    log(f"starting training run with train datasets={list(train_datasets)}")
    log(f"using dev datasets={list(dev_datasets)}")
    train_sentences, train_stats = load_split_with_cache(
        train_datasets,
        "train",
        cache_dir=cache_dir,
    )
    log(
        f"finished train preparation with {len(train_sentences)} sentences "
        f"in {format_seconds(time.perf_counter() - overall_started_at)}"
    )
    dev_started_at = time.perf_counter()
    dev_sentences, dev_stats = load_split_with_cache(
        dev_datasets,
        "dev",
        cache_dir=cache_dir,
    )
    log(
        f"finished dev preparation with {len(dev_sentences)} sentences "
        f"in {format_seconds(time.perf_counter() - dev_started_at)}"
    )
    train_x, train_y = to_xy(train_sentences)
    dev_x, dev_y = to_xy(dev_sentences)
    log(
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

    smoke_test = build_smoke_test(model, float(best_row["threshold"]))
    manifest = build_manifest(
        model=model,
        artifact_version=artifact_version,
        model_name=model_name,
        best_row=best_row,
        train_datasets=train_datasets,
        dev_datasets=dev_datasets,
        train_stats=train_stats,
        dev_stats=dev_stats,
        smoke_test=smoke_test,
    )
    if (artifact_dir / MODEL_NAME).exists():
        (artifact_dir / MODEL_NAME).unlink()
    readme = model_card(
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
        smoke_test=smoke_test,
        readme=readme,
    )
    log(
        f"wrote model bundle to {artifact_dir} in "
        f"{format_seconds(time.perf_counter() - overall_started_at)}"
    )
    return manifest


def build_smoke_test(model: Any, threshold: float) -> dict[str, Any]:
    """Run the dependency-backed smoke prediction saved with the bundle."""
    smoke_input = preprocess(PreprocessingInput(text="هاذا كتاب جميل . "))
    log("running smoke prediction")
    smoke_predictions = predict_with_threshold(
        model,
        [sentence_features(smoke_input.tokens, smoke_input.morph_features)],
        threshold,
    )[0]
    return {
        "tokens": [token.form for token in smoke_input.tokens],
        "predictions": smoke_predictions,
    }


def build_manifest(
    *,
    model: Any,
    artifact_version: str,
    model_name: str,
    best_row: dict[str, Any],
    train_datasets: Sequence[str],
    dev_datasets: Sequence[str],
    train_stats: dict[str, dict[str, int]],
    dev_stats: dict[str, dict[str, int]],
    smoke_test: dict[str, Any],
) -> dict[str, Any]:
    """Build model, data, runtime, and inference metadata for the bundle."""
    return {
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
        "smoke_test": smoke_test,
    }


def model_card(
    *,
    manifest: dict[str, Any],
    dataset_names: Sequence[str],
    dev_dataset_names: Sequence[str],
    best_row: dict[str, Any],
) -> str:
    """Render the README/model card saved inside the artifact bundle."""
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
