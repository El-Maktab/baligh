"""Script to tune the Word N-Gram NWP model using Perplexity on the Validation Split."""

import argparse
import logging
import math

from src.services.nws.features.nwp.word_ngram.counter import NGramCounter
from src.services.nws.features.nwp.word_ngram.dataset import get_eval_stream
from src.services.nws.features.nwp.word_ngram.model import WordNGramLM
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
    parser = argparse.ArgumentParser(description="Tune Word N-Gram model.")
    parser.add_argument("--dataset", type=str, default="CALM/arwiki")
    parser.add_argument("--train-rows", type=int, default=10000)
    parser.add_argument("--val-rows", type=int, default=2000)

    args = parser.parse_args()

    logger.info("Building dataset cache...")

    train_stream = get_eval_stream(dataset_name=args.dataset, split_type="train")
    train_texts = []
    for i, text in enumerate(
        tqdm(train_stream, desc="Caching Train", total=args.train_rows)
    ):
        if i >= args.train_rows:
            break
        train_texts.append(text)

    val_stream = get_eval_stream(dataset_name=args.dataset, split_type="val")
    val_texts = []
    for i, text in enumerate(tqdm(val_stream, desc="Caching Val", total=args.val_rows)):
        if i >= args.val_rows:
            break
        val_texts.append(text)

    vocab = Vocabulary()

    configs = [
        {"max_n": 2, "min_count": 1},
        {"max_n": 3, "min_count": 1},
        {"max_n": 3, "min_count": 3},
    ]

    for config in configs:
        logger.info(f"--- Testing config: {config} ---")
        counter = NGramCounter(max_n=config["max_n"])

        for text in train_texts:
            tokens = tokenize_text(text)
            token_ids = [vocab.word_to_id(t) for t in tokens]
            counter.add_sequence(token_ids)

        smoother = KneserNeySmoother(counter)
        model_data = smoother.build_model(
            min_count=config["min_count"], min_n_to_prune=3
        )
        model = WordNGramLM(model_data)

        total_log_prob = 0.0
        total_words = 0

        for text in val_texts:
            tokens = tokenize_text(text)
            if not tokens:
                continue

            avg_log_prob = model.score_sequence(tokens)
            total_log_prob += avg_log_prob * len(tokens)
            total_words += len(tokens)

        if total_words > 0:
            avg_cross_entropy = -(total_log_prob / total_words)
            perplexity = math.exp(avg_cross_entropy)
            logger.info(
                f"Results -> PPL: {perplexity:.2f} (Total Words evaluated: {total_words})"
            )
        else:
            logger.info("No validation words found!")


if __name__ == "__main__":
    main()
