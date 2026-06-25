import numpy as np


def compute_metrics(eval_preds, ignore_index=-100):
    predictions, label_ids = eval_preds
    pred_ids = np.argmax(predictions, axis=-1)

    mask = label_ids != ignore_index
    filtered_preds = pred_ids[mask]
    filtered_labels = label_ids[mask]

    correct = int((filtered_preds == filtered_labels).sum())
    total = len(filtered_labels)
    accuracy = correct / total if total > 0 else 0.0

    tp = fp = fn = 0
    for pred, gold in zip(filtered_preds.tolist(), filtered_labels.tolist()):
        if pred == gold:
            tp += 1
        else:
            fp += 1
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    beta_sq = 0.25
    f05 = (
        (1 + beta_sq) * precision * recall / (beta_sq * precision + recall)
        if (beta_sq * precision + recall) > 0
        else 0.0
    )

    return {"accuracy": accuracy, "precision": precision, "recall": recall, "f05": f05}
