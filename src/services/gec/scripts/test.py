"""Evaluate a trained GEC edit-tagger model on the QALB-2014-L1 test set.

Pipeline:
1. Build test .sent/.cor → JSONL via the feature pipeline (with checkpointing)
2. Load trained model checkpoint
3. Run inference
4. Compute token-level metrics (accuracy, precision, recall, F0.5)
5. Print per-label breakdown, operation-type macro metrics, and sample predictions
"""

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorForTokenClassification,
)

from src.services.gec.config import (
    LABEL2ID_PATH,
    MIN_LABEL_FREQUENCY,
    PROCESSED_DATA_DIR,
)
from src.services.gec.features.common import build_feature_builder
from src.services.gec.features.pruner import LabelPruner
from src.services.gec.modules.edit_tagger.training.datasets import GECTrainingDataset

IGNORE_INDEX = -100
BETA_SQ = 0.25

RAW_DATA_DIR = PROCESSED_DATA_DIR.parent / "raw"
DEFAULT_TEST_SENT = RAW_DATA_DIR / "test" / "QALB-2014-L1-Test.sent"
DEFAULT_TEST_COR = RAW_DATA_DIR / "test" / "QALB-2014-L1-Test.cor"
DEFAULT_TEST_JSONL = PROCESSED_DATA_DIR / "test_tokens_labels.jsonl"


def build_test_data(sent_path: Path, cor_path: Path, jsonl_path: Path, force: bool = False):
    if not force and jsonl_path.exists():
        print(f"Test JSONL already exists at {jsonl_path}")
        return
    builder = build_feature_builder()
    test_examples = builder.build_pipeline(sent_path, cor_path, jsonl_path)
    print(f"Built {len(test_examples)} test examples")

    pruner = LabelPruner(min_frequency=MIN_LABEL_FREQUENCY)
    test_examples = pruner.prune(test_examples)
    print(f"After pruning: {len(test_examples)} test examples")


def run_inference(model, test_dataset, tokenizer, batch_size: int, device: torch.device):
    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        collate_fn=data_collator,
        shuffle=False,
    )

    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch in tqdm(test_loader, desc="Evaluating"):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"]

            logits = model(input_ids=input_ids, attention_mask=attention_mask).logits
            pred_ids = torch.argmax(logits, dim=-1).cpu().numpy()

            all_preds.append(pred_ids)
            all_labels.append(labels.numpy())

    return np.concatenate(all_preds, axis=0), np.concatenate(all_labels, axis=0)


def compute_overall_metrics(preds: np.ndarray, labels: np.ndarray):
    mask = labels != IGNORE_INDEX
    filtered_preds = preds[mask]
    filtered_labels = labels[mask]

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
    f05 = (
        (1 + BETA_SQ) * precision * recall / (BETA_SQ * precision + recall)
        if (BETA_SQ * precision + recall) > 0
        else 0.0
    )

    print("=" * 50)
    print(f"{'Metric':<20} {'Value':>10}")
    print("-" * 50)
    print(f"{'Total tokens':<20} {total:>10}")
    print(f"{'Correct':<20} {correct:>10}")
    print(f"{'Accuracy':<20} {accuracy:>10.4f}")
    print(f"{'Precision':<20} {precision:>10.4f}")
    print(f"{'Recall':<20} {recall:>10.4f}")
    print(f"{'F0.5':<20} {f05:>10.4f}")
    print("=" * 50)

    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f05": f05,
        "filtered_preds": filtered_preds,
        "filtered_labels": filtered_labels,
    }


def compute_per_label_metrics(filtered_preds, filtered_labels, id2label: dict, top_n: int = 50):
    label_tp: Counter = Counter()
    label_fp: Counter = Counter()
    label_fn: Counter = Counter()
    label_support: Counter = Counter()

    for pred, gold in zip(filtered_preds.tolist(), filtered_labels.tolist()):
        gold_name = id2label.get(gold, "[UNKNOWN]")
        pred_name = id2label.get(pred, "[UNKNOWN]")
        label_support[gold_name] += 1
        if pred == gold:
            label_tp[gold_name] += 1
        else:
            label_fp[pred_name] += 1
            label_fn[gold_name] += 1

    rows = []
    for label in sorted(label_support.keys(), key=lambda l: label_support[l], reverse=True):
        tp = label_tp[label]
        fp = label_fp.get(label, 0)
        fn = label_fn.get(label, 0)
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f = (1 + BETA_SQ) * p * r / (BETA_SQ * p + r) if (BETA_SQ * p + r) > 0 else 0.0
        rows.append((label, label_support[label], p, r, f))

    print(f"\n{'Label':<40} {'Support':>8} {'Prec':>8} {'Rec':>8} {'F0.5':>8}")
    print("-" * 80)
    for label, support, p, r, f in rows[:top_n]:
        print(f"{label:<40} {support:>8} {p:>8.4f} {r:>8.4f} {f:>8.4f}")
    if len(rows) > top_n:
        print(f"\n... and {len(rows) - top_n} more labels")


def get_op(label_name: str) -> str:
    if label_name.startswith("K") or label_name.startswith("[PAD") or label_name.startswith("[UNK"):
        return "KEEP"
    if label_name.startswith("R_"):
        return "REPLACE"
    if label_name.startswith("I_"):
        return "INSERT"
    if label_name.startswith("D"):
        return "DELETE"
    return "OTHER"


def compute_operation_metrics(filtered_preds, filtered_labels, id2label: dict):
    op_tp: Counter = Counter()
    op_fp: Counter = Counter()
    op_fn: Counter = Counter()
    op_support: Counter = Counter()

    for pred, gold in zip(filtered_preds.tolist(), filtered_labels.tolist()):
        gold_name = id2label.get(gold, "[UNKNOWN]")
        pred_name = id2label.get(pred, "[UNKNOWN]")
        gold_op = get_op(gold_name)
        pred_op = get_op(pred_name)

        op_support[gold_op] += 1
        if gold_op == pred_op:
            op_tp[gold_op] += 1
        else:
            op_fp[pred_op] += 1
            op_fn[gold_op] += 1

    print(f"\n{'Operation':<12} {'Support':>8} {'Prec':>8} {'Rec':>8} {'F0.5':>8}")
    print("-" * 56)
    for op in ["KEEP", "REPLACE", "INSERT", "DELETE", "OTHER"]:
        tp = op_tp.get(op, 0)
        fp = op_fp.get(op, 0)
        fn = op_fn.get(op, 0)
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f = (1 + BETA_SQ) * p * r / (BETA_SQ * p + r) if (BETA_SQ * p + r) > 0 else 0.0
        print(f"{op:<12} {op_support.get(op, 0):>8} {p:>8.4f} {r:>8.4f} {f:>8.4f}")


def print_sample_predictions(all_preds, id2label: dict, test_jsonl_path: Path, num_samples: int = 5):
    with test_jsonl_path.open(encoding="utf-8") as f:
        test_raw = [json.loads(line) for line in f if line.strip()]

    for i in range(min(num_samples, len(test_raw))):
        subwords = test_raw[i]["subwords"]
        gold_labels = test_raw[i].get("labels_star", test_raw[i].get("labels", []))

        pred_ids_i = all_preds[i][: len(subwords)]
        pred_names = [id2label.get(pid, "[UNK]") for pid in pred_ids_i]

        print(f"\n--- Example {i + 1} ---")
        mismatches = 0
        total_toks = 0
        for sw, gl, pl in zip(subwords, gold_labels, pred_names):
            if gl != pl:
                mismatches += 1
            total_toks += 1
        print(
            f"Token accuracy: {1 - mismatches / total_toks:.4f} ({total_toks - mismatches}/{total_toks})"
        )
        print()
        print(f"{'Subword':<20} {'Gold':<30} {'Pred':<30} {'Match'}")
        print("-" * 80)
        for sw, gl, pl in zip(subwords, gold_labels, pred_names):
            mark = "OK" if gl == pl else "WRONG"
            if gl != pl:
                print(f"{sw:<20} {gl:<30} {pl:<30} {mark}")
        print("\n(Showing only mismatched tokens above)")


def main():
    parser = argparse.ArgumentParser(description="Evaluate GEC edit-tagger on test set")
    parser.add_argument("--model_checkpoint", type=str, required=True, help="Path to model checkpoint dir")
    parser.add_argument("--base_checkpoint", default="aubmindlab/bert-base-arabertv02")
    parser.add_argument("--test_sent", default=str(DEFAULT_TEST_SENT))
    parser.add_argument("--test_cor", default=str(DEFAULT_TEST_COR))
    parser.add_argument("--test_jsonl", default=str(DEFAULT_TEST_JSONL))
    parser.add_argument("--label2id", default=str(LABEL2ID_PATH))
    parser.add_argument("--max_length", type=int, default=256)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--force_rebuild", action="store_true", help="Force rebuild test JSONL")
    parser.add_argument("--num_samples", type=int, default=5, help="Number of sample predictions to show")
    parser.add_argument("--top_labels", type=int, default=50, help="Top N labels in per-label breakdown")
    args = parser.parse_args()

    build_test_data(Path(args.test_sent), Path(args.test_cor), Path(args.test_jsonl), force=args.force_rebuild)

    with open(args.label2id, encoding="utf-8") as f:
        label2id = json.load(f)
    id2label = {v: k for k, v in label2id.items()}
    print(f"Label vocabulary: {len(label2id)} labels")

    tokenizer = AutoTokenizer.from_pretrained(args.base_checkpoint)

    test_dataset = GECTrainingDataset(
        jsonl_path=args.test_jsonl,
        tokenizer=tokenizer,
        label2id=label2id,
        max_length=args.max_length,
    )
    print(f"Test examples: {len(test_dataset)}")

    model = AutoModelForTokenClassification.from_pretrained(args.model_checkpoint)
    model.eval()
    print(f"Model loaded from {args.model_checkpoint}")
    print(f"num_labels = {model.config.num_labels}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    print(f"Device: {device}")

    all_preds, all_labels = run_inference(model, test_dataset, tokenizer, args.batch_size, device)
    print(f"Predictions shape: {all_preds.shape}")
    print(f"Labels shape: {all_labels.shape}")

    results = compute_overall_metrics(all_preds, all_labels)
    compute_per_label_metrics(results["filtered_preds"], results["filtered_labels"], id2label, top_n=args.top_labels)
    compute_operation_metrics(results["filtered_preds"], results["filtered_labels"], id2label)
    print_sample_predictions(all_preds, id2label, Path(args.test_jsonl), num_samples=args.num_samples)


if __name__ == "__main__":
    main()
