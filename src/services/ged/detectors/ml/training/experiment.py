"""CRF fitting and threshold selection for GED ML training.

Authors:
    Amir Anwar
"""

from __future__ import annotations

import time
from collections.abc import Iterable, Sequence
from typing import Any

from sklearn_crfsuite import CRF

from src.services.ged.detectors.ml.labels import NO_ERROR
from src.services.ged.detectors.ml.training.logging import format_seconds, log
from src.services.ged.evaluation.metrics import calculate_metrics


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
                log(
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
                log(
                    "finished CRF fit "
                    f"(c1={c1}, c2={c2}, max_iterations={max_iterations}) in "
                    f"{format_seconds(time.perf_counter() - fit_started_at)}"
                )
                threshold_started_at = time.perf_counter()
                log("starting threshold sweep")
                sweep, row = evaluate_thresholds(model, dev_x, dev_y, thresholds)
                log(
                    "finished threshold sweep in "
                    f"{format_seconds(time.perf_counter() - threshold_started_at)}; "
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


def _predictions_to_sets(labels: Sequence[str]) -> list[set[str]]:
    return [set() if label == NO_ERROR else {label} for label in labels]
