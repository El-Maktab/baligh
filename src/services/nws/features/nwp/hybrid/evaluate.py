"""Evaluation script for the Hybrid NWP model.

Authors:
    Akram Hany
"""

import random

import torch
from loguru import logger
from src.services.nws.features.nwp.hybrid.model import HybridArabicPredictor
from src.services.nws.features.nwp.lstm.fetch_wiki_mad import normalise_arabic
from src.services.nws.features.nwp.lstm.model import LSTMNWPModel
from src.services.nws.features.nwp.word_ngram.model import WordNGramLM
from src.services.nws.features.nwp.word_ngram.serializer import load_ngram_model
from tqdm import tqdm


def run_hybrid_evaluation(num_samples: int = 2000, seed: int = 42):
    """Evaluates the HybridArabicPredictor on a random sample of word-level contexts."""
    random.seed(seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    base_dir = "src/services/nws/data"
    test_file = f"{base_dir}/lstm_corpus/corpus_test.txt"

    # Load N-Gram
    logger.info("Loading N-Gram model.")
    ngram_data = load_ngram_model(f"{base_dir}/word_ngram_lm_lstm.msgpack.gz")
    kn_model = WordNGramLM(ngram_data)

    # Load LSTM
    logger.info("Loading LSTM model.")
    neural_model = LSTMNWPModel(
        model_path=f"{base_dir}/best_model.pt",
        sp_model_path=f"{base_dir}/arabic_bpe.model",
    )

    hybrid = HybridArabicPredictor(neural_model, kn_model)

    logger.info("Extracting pairs.")
    pairs = []
    with open(test_file, encoding="utf-8") as f:
        for line in f:
            words = line.strip().split()
            # Need 2+ words
            if len(words) < 2:
                continue

            for i in range(1, len(words)):
                context = " ".join(words[:i]) + " "
                target = words[i]

                if target in ("<s>", "</s>"):
                    continue

                pairs.append((context, target))

    logger.info(f"Total pairs: {len(pairs)}")

    sampled_pairs = random.sample(pairs, min(num_samples, len(pairs)))
    logger.info(f"Evaluating {len(sampled_pairs)} pairs.")

    top_1 = 0
    top_3 = 0
    top_5 = 0

    for context, target in tqdm(sampled_pairs, desc="Evaluating Hybrid"):
        norm_context = normalise_arabic(context)
        if context.endswith(" "):
            norm_context += " "

        norm_target = normalise_arabic(target)

        predictions = hybrid.predict(norm_context, top_k=5)
        pred_words = [word for word, score in predictions]

        if len(pred_words) >= 1 and pred_words[0] == norm_target:
            top_1 += 1
        if norm_target in pred_words[:3]:
            top_3 += 1
        if norm_target in pred_words[:5]:
            top_5 += 1

    acc_1 = top_1 / len(sampled_pairs)
    acc_3 = top_3 / len(sampled_pairs)
    acc_5 = top_5 / len(sampled_pairs)

    print("\n--- Hybrid Model Evaluation Results ---")
    print(f"Top-1 Word Accuracy: {acc_1:.2%}")
    print(f"Top-3 Word Accuracy: {acc_3:.2%}")
    print(f"Top-5 Word Accuracy: {acc_5:.2%}")


if __name__ == "__main__":
    run_hybrid_evaluation(num_samples=2500)
