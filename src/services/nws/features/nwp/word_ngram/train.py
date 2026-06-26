"""Script to train the Word N-Gram NWP model."""

import argparse
import logging
from pathlib import Path

from src.services.nws.features.nwp.word_ngram.counter import NGramCounter
from src.services.nws.features.nwp.word_ngram.dataset import get_eval_stream
from src.services.nws.features.nwp.word_ngram.serializer import save_ngram_model
from src.services.nws.features.nwp.word_ngram.smoother import KneserNeySmoother
from src.services.nws.features.nwp.word_ngram.tokenizer import tokenize_text
from src.services.nws.features.nwp.word_ngram.vocab import Vocabulary
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Train Word N-Gram model.")
    parser.add_argument(
        "--dataset", type=str, default="CALM/arwiki", help="HuggingFace dataset name"
    )
    parser.add_argument(
        "--max-rows", type=int, default=100000, help="Maximum number of rows to process"
    )
    parser.add_argument("--max-n", type=int, default=3, help="Maximum N-Gram order")
    parser.add_argument("--min-count", type=int, default=3, help="Prune threshold")
    parser.add_argument(
        "--output", type=str, required=True, help="Output path for the .msgpack.gz file"
    )

    args = parser.parse_args()

    logger.info(f"Starting training with max_rows={args.max_rows}, max_n={args.max_n}")

    counter = NGramCounter(max_n=args.max_n)
    vocab = Vocabulary()

    stream = get_eval_stream(dataset_name=args.dataset, split_type="train")

    rows_processed = 0
    words_processed = 0

    pbar = tqdm(total=args.max_rows, desc="Processing rows")

    for row_text in stream:
        if rows_processed >= args.max_rows:
            break

        tokens = tokenize_text(row_text)
        token_ids = [vocab.word_to_id(t) for t in tokens]

        counter.add_sequence(token_ids)

        words_processed += len(token_ids)
        rows_processed += 1
        pbar.update(1)

    pbar.close()

    logger.info(f"Processed {rows_processed} rows, {words_processed} words.")
    logger.info("Applying Kneser-Ney Smoothing and Pruning...")

    smoother = KneserNeySmoother(counter)
    model_data = smoother.build_model(min_count=args.min_count, min_n_to_prune=3)

    logger.info(f"Saving model to {args.output}...")
    save_ngram_model(model_data, Path(args.output))
    logger.info("Training complete!")


if __name__ == "__main__":
    main()
