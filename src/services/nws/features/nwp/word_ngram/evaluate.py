"""Script to evaluate the Word N-Gram NWP model."""

import argparse
import json
import logging
import math
import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
while current_dir.name and not (current_dir / "pyproject.toml").exists():
    current_dir = current_dir.parent
sys.path.append(str(current_dir))

from src.services.nws.features.nwp.word_ngram.dataset import get_eval_stream
from src.services.nws.features.nwp.word_ngram.model import WordNGramLM
from src.services.nws.features.nwp.word_ngram.serializer import load_ngram_model
from src.services.nws.features.nwp.word_ngram.tokenizer import tokenize_text
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Evaluate Word N-Gram model.")
    parser.add_argument("--dataset", type=str, default="CALM/arwiki")
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--test-rows", type=int, default=5000)
    parser.add_argument(
        "--output", type=str, default="artifacts/nws/evaluation/nwp/report.json"
    )

    args = parser.parse_args()

    logger.info(f"Loading model from {args.model}...")
    model_data = load_ngram_model(Path(args.model))
    model = WordNGramLM(model_data)

    logger.info("Building Test dataset stream...")
    test_stream = get_eval_stream(dataset_name=args.dataset, split_type="test")

    total_log_prob = 0.0
    total_tokens_scored = 0

    top_1_hits = 0
    top_3_hits = 0
    top_5_hits = 0
    mrr_sum = 0.0
    prediction_events = 0

    for i, text in enumerate(
        tqdm(test_stream, desc="Evaluating", total=args.test_rows)
    ):
        if i >= args.test_rows:
            break

        # FIX 1: Truncate RAW TEXT before tokenizing
        # ~6 chars per Arabic word on average -> 10,000 words ≈ 60,000 chars
        # This avoids tokenizing 500k+ words just to throw 98% away.
        CHAR_LIMIT = 60_000
        text = text[:CHAR_LIMIT]

        tokens = tokenize_text(text)
        if len(tokens) < 2:
            continue

        # FIX 3: Sample every Nth token for prediction accuracy.
        # This reduces predict_next() calls by 5x while retaining statistical validity.
        SAMPLE_EVERY = 5

        log_prob_sum = 0.0
        tokens_scored = 0

        # FIX 2: Merge perplexity + accuracy into ONE loop.
        for j in range(1, len(tokens)):
            max_history = model.max_n - 1
            context = tokens[max(0, j - max_history) : j]
            target = tokens[j]

            # Perplexity: score every token
            token_log_prob = model.score_token(context, target)
            log_prob_sum += token_log_prob
            tokens_scored += 1

            # Accuracy: only on sampled, non-special tokens
            if j % SAMPLE_EVERY != 0:
                continue

            # Skip predicting special tokens or punctuation for accuracy metrics
            if (
                target in ["<s>", "</s>", "<unk>"]
                or target in model.vocab._reverse_punct.values()
            ):
                continue

            predictions = model.predict_next(context, top_k=5)
            prediction_events += 1

            if target in predictions:
                rank = predictions.index(target) + 1
                if rank == 1:
                    top_1_hits += 1
                if rank <= 3:
                    top_3_hits += 1
                if rank <= 5:
                    top_5_hits += 1
                mrr_sum += 1.0 / rank

        total_log_prob += log_prob_sum
        total_tokens_scored += tokens_scored

    if total_tokens_scored > 0:
        ppl = math.exp(-(total_log_prob / total_tokens_scored))
    else:
        ppl = float("inf")

    metrics = {
        "dataset": args.dataset,
        "test_rows_processed": args.test_rows,
        "perplexity": ppl,
        "prediction_events": prediction_events,
        "top_1_accuracy": (top_1_hits / prediction_events)
        if prediction_events
        else 0.0,
        "top_3_accuracy": (top_3_hits / prediction_events)
        if prediction_events
        else 0.0,
        "top_5_accuracy": (top_5_hits / prediction_events)
        if prediction_events
        else 0.0,
        "mrr": (mrr_sum / prediction_events) if prediction_events else 0.0,
    }

    logger.info("Evaluation Complete!")
    logger.info(json.dumps(metrics, indent=4))

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4)


if __name__ == "__main__":
    main()
