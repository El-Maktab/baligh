"""Evaluation metrics for the GEC edit-tagger model."""

import numpy as np


def compute_metrics(eval_preds, id2label: dict[int, str], ignore_index: int = -100) -> dict[str, float]:
    """Compute token-level precision, recall, and F0.5 from model logits.

    This callback is designed to be used with HuggingFace ``Trainer``. It
    decodes predicted label IDs and gold label IDs into their string
    representations, then computes micro-averaged metrics over all
    non-ignored positions.

    Args:
        eval_preds: ``EvalPrediction`` object with ``predictions`` and
            ``label_ids`` arrays.
        id2label: Mapping from integer label ID to string tag.
        ignore_index: Label ID that marks positions to skip (default -100).

    Returns:
        Dictionary with ``accuracy``, ``precision``, ``recall``, and ``f05``.
    """
    predictions, label_ids = eval_preds
    pred_ids = np.argmax(predictions, axis=-1)

    mask = label_ids != ignore_index

    filtered_preds = pred_ids[mask]
    filtered_labels = label_ids[mask]

    correct = int((filtered_preds == filtered_labels).sum())
    total = len(filtered_labels)

    accuracy = correct / total if total > 0 else 0.0

    tp: dict[str, int] = {}
    fp: dict[str, int] = {}
    fn: dict[str, int] = {}

    for pred, gold in zip(filtered_preds.tolist(), filtered_labels.tolist()):
        pred_label = id2label.get(pred, "[UNK]")
        gold_label = id2label.get(gold, "[UNK]")

        if pred_label == gold_label:
            tp[pred_label] = tp.get(pred_label, 0) + 1
        else:
            fp[pred_label] = fp.get(pred_label, 0) + 1
            fn[gold_label] = fn.get(gold_label, 0) + 1

    total_tp = sum(tp.values())
    total_fp = sum(fp.values())
    total_fn = sum(fn.values())

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0

    beta = 0.5
    beta_sq = beta ** 2
    f05 = (
        (1 + beta_sq) * precision * recall / (beta_sq * precision + recall)
        if (beta_sq * precision + recall) > 0
        else 0.0
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f05": f05,
    }
