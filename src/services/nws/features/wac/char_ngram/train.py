"""Training script for the Character N-gram LM.

Authors:
    Akram Hany
"""

import argparse
import logging
import sys
from pathlib import Path

from src.services.nws.features.wac.char_ngram.counter import NGramCounter
from src.services.nws.features.wac.char_ngram.dataset import (
    get_eval_stream,
)
from src.services.nws.features.wac.char_ngram.serializer import save_model
from src.services.nws.features.wac.char_ngram.smoother import (
    KneserNeySmoother,
)
from tqdm import tqdm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    """Train the Character N-gram LM."""
    parser = argparse.ArgumentParser(description="Train Character N-gram LM")
    parser.add_argument(
        "--dataset",
        type=str,
        default="CALM/arwiki",
        help="HuggingFace dataset to train on.",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=50_000_000,
        help="Maximum number of characters to process (50M chars ≈ 100MB of raw text).",
    )
    parser.add_argument(
        "--max-n", type=int, default=5, help="Maximum n-gram order (default: 5)."
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=3,
        help="Minimum count for pruning (default: 3).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="src/services/nws/data/char_ngram_lm.msgpack.gz",
        help="Output path for the trained model.",
    )
    args = parser.parse_args()

    logger.info(f"Training max_chars={args.max_chars}, max_n={args.max_n}")

    # Initialize counter
    counter = NGramCounter(max_n=args.max_n)

    # Stream dataset
    logger.info(f"Loading dataset: {args.dataset}")
    text_stream = get_eval_stream(
        dataset_name=args.dataset, split_type="train", limit_chars=args.max_chars
    )

    chars_processed = 0
    pbar = tqdm(total=args.max_chars, desc="Processing characters")

    for clean_text in text_stream:
        counter.add_sequence(clean_text)
        chars_processed += len(clean_text)
        pbar.update(len(clean_text))

    pbar.close()
    logger.info(f"Processed chars: {chars_processed}")

    # Smoothing and Pruning
    logger.info("Initializing smoother")
    smoother = KneserNeySmoother(counter)

    logger.info(f"Building model (min_count={args.min_count})")
    # Build model from unpruned counts for correct lambdas
    model_data = smoother.build_model(min_count=args.min_count, min_n_to_prune=3)

    # Serialize
    out_path = Path(args.output)
    save_model(model_data, out_path)

    # Verify file
    if out_path.exists():
        size_mb = out_path.stat().st_size / (1024 * 1024)
        logger.info(f"Model saved: {out_path} ({size_mb:.2f} MB)")
    else:
        logger.error("Failed to save model")
        sys.exit(1)


if __name__ == "__main__":
    main()
