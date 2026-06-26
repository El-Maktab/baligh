"""Module docstring."""

import argparse
import logging
import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
while current_dir.name and not (current_dir / "pyproject.toml").exists():
    current_dir = current_dir.parent
sys.path.append(str(current_dir))  # noqa: E402
from src.services.nws.features.wac.char_ngram.counter import NGramCounter  # noqa: E402
from src.services.nws.features.wac.char_ngram.dataset import (  # noqa: E402
    generate_prefix_pairs,
    get_eval_stream,
)
from src.services.nws.features.wac.char_ngram.metrics import (  # noqa: E402
    compute_perplexity,
    mean_reciprocal_rank,
)
from src.services.nws.features.wac.char_ngram.model import CharNGramLM  # noqa: E402
from src.services.nws.features.wac.char_ngram.smoother import (
    KneserNeySmoother,  # noqa: E402
)
from tqdm import tqdm  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    """Function docstring."""
    parser = argparse.ArgumentParser()
    # Use smaller defaults to keep tuning relatively fast
    parser.add_argument("--train-chars", type=int, default=1_000_000)
    parser.add_argument("--val-chars", type=int, default=100_000)
    args = parser.parse_args()

    logger.info("Gathering Training stream...")
    train_stream = get_eval_stream(split_type="train", limit_chars=args.train_chars)
    counter = NGramCounter(max_n=5)
    for text in tqdm(train_stream, desc="Counting train"):
        counter.add_sequence(text)

    logger.info("Initializing Smoother...")
    smoother = KneserNeySmoother(counter)

    logger.info("Gathering Val stream for Perplexity...")
    val_texts = list(get_eval_stream(split_type="val", limit_chars=args.val_chars))

    logger.info("--- Stage 4: Tuning Cutoff (min_count) ---")
    best_cutoff = 1
    best_ppl = float("inf")

    for cutoff in [1, 2, 3, 5, 10]:
        model_data = smoother.build_model(min_count=cutoff, min_n_to_prune=3)
        model = CharNGramLM(model_data)
        bpc, ppl, _ = compute_perplexity(model, val_texts)
        logger.info(f"Cutoff={cutoff} -> Perplexity={ppl:.4f} (BPC={bpc:.4f})")
        if ppl < best_ppl:
            best_ppl = ppl
            best_cutoff = cutoff

    logger.info(f"Selected best Cutoff: {best_cutoff}")

    # Rebuild final best model
    best_model_data = smoother.build_model(min_count=best_cutoff, min_n_to_prune=3)
    best_model = CharNGramLM(best_model_data)

    logger.info("--- Stage 4: Tuning Top-K ---")
    val_pairs = []
    for text in val_texts:
        val_pairs.extend(generate_prefix_pairs(text))

    val_pairs = val_pairs[:1000]  # Cap for speed

    best_k = 1
    best_mrr = 0.0
    for k in [1, 3, 5, 8, 10]:
        mrr = mean_reciprocal_rank(
            tqdm(val_pairs, desc=f"Eval K={k}"), best_model, max_k=k
        )
        logger.info(f"Top-K={k} -> MRR={mrr:.4f}")
        if mrr > best_mrr:
            best_mrr = mrr
            best_k = k

    logger.info(f"Selected best Top-K: {best_k}")
    logger.info(
        f"Tuning complete. Recommended settings: min_count={best_cutoff}, top_k={best_k}"
    )


if __name__ == "__main__":
    main()
