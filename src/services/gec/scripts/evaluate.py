"""Evaluate a trained GEC edit-tagger model on the QALB-2014-L1 test set."""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from loguru import logger
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorForTokenClassification,
)

from src.runtime_config import load_runtime_config
from src.services.gec.features.common import build_feature_builder
from src.services.gec.features.pruner import LabelPruner
from src.services.gec.modules.edit_tagger.training.datasets import GECTrainingDataset

_EDIT_TAGGER = load_runtime_config().gec.edit_tagger
LABEL2ID_PATH = _EDIT_TAGGER.resolved_label2id_path
MIN_LABEL_FREQUENCY = _EDIT_TAGGER.min_label_frequency
PROCESSED_DATA_DIR = _EDIT_TAGGER.resolved_processed_data_dir

IGNORE_INDEX = -100
BETA_SQ = 0.25

RAW_DATA_DIR = PROCESSED_DATA_DIR.parent / "raw"
DEFAULT_TEST_SENT = RAW_DATA_DIR / "test" / "QALB-2014-L1-Test.sent"
DEFAULT_TEST_COR = RAW_DATA_DIR / "test" / "QALB-2014-L1-Test.cor"
DEFAULT_TEST_JSONL = PROCESSED_DATA_DIR / "test_tokens_labels.jsonl"


def build_test_data(
    sent_path: Path, cor_path: Path, jsonl_path: Path, force: bool = False
):
    """Build test features from raw sent/cor files if the JSONL does not exist."""
    if not force and jsonl_path.exists():
        logger.info(f"Test JSONL already exists at {jsonl_path}")
        return
    builder = build_feature_builder()
    test_examples = builder.build_pipeline(sent_path, cor_path, jsonl_path)
    logger.info(f"Built {len(test_examples)} test examples")

    pruner = LabelPruner(min_frequency=MIN_LABEL_FREQUENCY)
    test_examples = pruner.prune(test_examples)
    logger.info(f"After pruning: {len(test_examples)} test examples")


def run_inference(
    model, test_dataset, tokenizer, batch_size: int, device: torch.device
):
    """Run model inference on the test dataset and return predictions and labels."""
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
            labels = batch["labels"].numpy()

            logits = model(input_ids=input_ids, attention_mask=attention_mask).logits
            preds = torch.argmax(logits, dim=-1).cpu().numpy()
            mask = labels != -100

            all_preds.extend(preds[mask])
            all_labels.extend(labels[mask])

    return np.array(all_preds), np.array(all_labels)


def compute_overall_metrics(preds: np.ndarray, labels: np.ndarray):
    """Compute and log overall accuracy, precision, recall, and F0.5."""
    mask = labels != IGNORE_INDEX
    filtered_preds = preds[mask]
    filtered_labels = labels[mask]

    correct = int((filtered_preds == filtered_labels).sum())
    total = len(filtered_labels)
    accuracy = correct / total if total > 0 else 0.0

    tp = fp = fn = 0
    for pred, gold in zip(
        filtered_preds.tolist(), filtered_labels.tolist(), strict=False
    ):
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

    logger.info("=" * 50)
    logger.info(f"{'Metric':<20} {'Value':>10}")
    logger.info("-" * 50)
    logger.info(f"{'Total tokens':<20} {total:>10}")
    logger.info(f"{'Correct':<20} {correct:>10}")
    logger.info(f"{'Accuracy':<20} {accuracy:>10.4f}")
    logger.info(f"{'Precision':<20} {precision:>10.4f}")
    logger.info(f"{'Recall':<20} {recall:>10.4f}")
    logger.info(f"{'F0.5':<20} {f05:>10.4f}")
    logger.info("=" * 50)

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


def main():
    """Parse arguments and run the evaluation pipeline."""
    parser = argparse.ArgumentParser(description="Evaluate GEC edit-tagger on test set")
    parser.add_argument("--model_checkpoint", type=str, required=True)
    parser.add_argument("--base_checkpoint", default="aubmindlab/bert-base-arabertv02")
    parser.add_argument("--test_sent", default=str(DEFAULT_TEST_SENT))
    parser.add_argument("--test_cor", default=str(DEFAULT_TEST_COR))
    parser.add_argument("--test_jsonl", default=str(DEFAULT_TEST_JSONL))
    parser.add_argument("--label2id", default=str(LABEL2ID_PATH))
    parser.add_argument("--max_length", type=int, default=256)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--force_rebuild", action="store_true")
    parser.add_argument("--num_samples", type=int, default=5)
    parser.add_argument("--top_labels", type=int, default=15)
    args = parser.parse_args()

    build_test_data(
        Path(args.test_sent),
        Path(args.test_cor),
        Path(args.test_jsonl),
        force=args.force_rebuild,
    )

    with open(args.label2id, encoding="utf-8") as f:
        label2id = json.load(f)
    logger.info(f"Label vocabulary: {len(label2id)}")

    tokenizer = AutoTokenizer.from_pretrained(args.base_checkpoint)

    test_dataset = GECTrainingDataset(
        jsonl_path=args.test_jsonl,
        tokenizer=tokenizer,
        label2id=label2id,
        max_length=args.max_length,
    )
    logger.info(f"Test examples: {len(test_dataset)}")

    model = AutoModelForTokenClassification.from_pretrained(args.model_checkpoint)
    model.eval()
    logger.info(f"Model loaded from {args.model_checkpoint}")
    logger.info(f"num_labels = {model.config.num_labels}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    logger.info(f"Device: {device}")

    all_preds, all_labels = run_inference(
        model, test_dataset, tokenizer, args.batch_size, device
    )
    logger.info(f"Predictions shape: {all_preds.shape}")
    logger.info(f"Labels shape: {all_labels.shape}")

    _results = compute_overall_metrics(all_preds, all_labels)


if __name__ == "__main__":
    main()
