"""Evaluation module for character n-gram language models.

Authors:
    Akram Hany
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path  # noqa: E402

from src.services.nws.features.wac.char_ngram.dataset import (  # noqa: E402
    generate_prefix_pairs,
    get_eval_stream,
)
from src.services.nws.features.wac.char_ngram.model import CharNGramLM  # noqa: E402
from src.services.nws.features.wac.char_ngram.serializer import load_model  # noqa: E402
from tqdm import tqdm  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    """Evaluate Char N-gram LM on Test Set."""
    parser = argparse.ArgumentParser(description="Evaluate Char N-gram LM on Test Set")
    parser.add_argument(
        "--dataset",
        type=str,
        default="CALM/arwiki",
        help="HuggingFace dataset to evaluate against.",
    )
    parser.add_argument(
        "--model", type=str, default="src/services/nws/data/char_ngram_lm.msgpack.gz"
    )
    parser.add_argument(
        "--top-k", type=int, default=5, help="Top-K used for KSR and final metrics"
    )
    parser.add_argument(
        "--limit-chars", type=int, default=500_000, help="Chars to use from test set"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/nws/evaluation/wac/char_ngram/report.json",
    )
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        logger.error(f"Model not found: {model_path}")
        sys.exit(1)

    logger.info("Loading model")
    model = CharNGramLM(load_model(model_path))

    logger.info("Loading test dataset")
    test_stream = get_eval_stream(
        dataset_name=args.dataset, split_type="test", limit_chars=args.limit_chars
    )

    logger.info("Generating prefix pairs")
    test_pairs = []
    # We load chunks into memory to generate pairs.
    for chunk in test_stream:
        test_pairs.extend(generate_prefix_pairs(chunk))

    logger.info(f"Pairs generated: {len(test_pairs)}")
    if not test_pairs:
        logger.error("No pairs generated")
        sys.exit(1)

    # Cap test pairs
    max_eval_pairs = 250
    if len(test_pairs) > max_eval_pairs:
        logger.info(f"Capped evaluation to {max_eval_pairs} pairs")
        test_pairs = test_pairs[:max_eval_pairs]

    logger.info("Computing metrics")
    hits_1, hits_3, hits_5 = 0, 0, 0
    rr_sum = 0.0
    ksr_total_without = 0
    ksr_total_with = 0

    pairs_by_len = defaultdict(list)

    for full_prefix, true_word, prefix_len in tqdm(test_pairs, desc="Evaluating"):
        predictions = model.predict(full_prefix, top_k=10)

        # Accuracy
        if true_word in predictions[:1]:
            hits_1 += 1
        if true_word in predictions[:3]:
            hits_3 += 1
        if true_word in predictions[:5]:
            hits_5 += 1

        # MRR
        if true_word in predictions:
            rank = predictions.index(true_word) + 1
            rr_sum += 1.0 / rank

        # KSR
        ksr_predictions = predictions[: args.top_k]
        ksr_without = len(true_word)
        if true_word in ksr_predictions:
            ksr_with = prefix_len + 1
        else:
            ksr_with = len(true_word)
        ksr_total_without += ksr_without
        ksr_total_with += ksr_with

        pairs_by_len[prefix_len].append((true_word, predictions[:5]))

    n_pairs = len(test_pairs)
    top_1 = hits_1 / n_pairs if n_pairs else 0.0
    top_3 = hits_3 / n_pairs if n_pairs else 0.0
    top_5 = hits_5 / n_pairs if n_pairs else 0.0
    mrr = rr_sum / n_pairs if n_pairs else 0.0
    ksr = 1.0 - (ksr_total_with / ksr_total_without) if ksr_total_without else 0.0

    logger.info("Evaluation results:")
    logger.info(f"Top-1 Accuracy: {top_1:.4f}")
    logger.info(f"Top-3 Accuracy: {top_3:.4f}")
    logger.info(f"Top-5 Accuracy: {top_5:.4f}")
    logger.info(f"MRR: {mrr:.4f}")
    logger.info(f"KSR (K={args.top_k}): {ksr:.4f}")

    logger.info("Computing prefix length breakdown")

    breakdown = {}
    for length in sorted(pairs_by_len.keys())[:10]:
        sub_pairs = pairs_by_len[length]
        sub_hits_5 = sum(1 for true_word, preds in sub_pairs if true_word in preds)
        sub_acc = sub_hits_5 / len(sub_pairs)
        breakdown[length] = {"count": len(sub_pairs), "top_5_acc": round(sub_acc, 4)}
        logger.info(
            f"Prefix length {length} Top-5 Acc: {sub_acc:.4f} (n={len(sub_pairs)})"
        )


if __name__ == "__main__":
    main()
