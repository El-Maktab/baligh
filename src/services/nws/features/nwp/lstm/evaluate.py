import json
import os
import random

import torch
from loguru import logger
from src.services.nws.features.nwp.lstm.fetch_wiki_mad import normalise_arabic
from src.services.nws.features.nwp.lstm.model import LSTMNWPModel
from tqdm import tqdm


def run_lstm_evaluation(num_samples: int = 2500, seed: int = 42):
    """Evaluates the LSTMNWPModel on a random sample of word-level contexts
    from the test set using full-word autoregressive beam search.
    """
    random.seed(seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    base_dir = "src/services/nws/data"
    test_file = f"{base_dir}/lstm_corpus/corpus_test.txt"

    # Load the LSTM Model
    logger.info("Loading LSTM Model...")
    neural_model = LSTMNWPModel(
        model_path=f"{base_dir}/best_model.pt",
        sp_model_path=f"{base_dir}/arabic_bpe.model",
    )

    # Prepare Context-Target pairs from Test Set
    logger.info("Extracting context-target pairs from test set...")
    pairs = []

    with open(test_file, encoding="utf-8") as f:
        for line in f:
            words = line.strip().split()
            # We need at least 2 words to form a context + target
            if len(words) < 2:
                continue

            for i in range(1, len(words)):
                context = " ".join(words[:i]) + " "
                target = words[i]

                # Exclude boundary markers if they bleed into target
                if target in ("<s>", "</s>"):
                    continue

                pairs.append((context, target))

    logger.info(f"Total word-level pairs available: {len(pairs)}")

    # Randomly sample to keep evaluation time reasonable
    sampled_pairs = random.sample(pairs, min(num_samples, len(pairs)))
    logger.info(
        f"Evaluating LSTM Predictor on {len(sampled_pairs)} sampled contexts..."
    )

    # Metrics
    top_1 = 0
    top_3 = 0
    top_5 = 0

    # Run Evaluation Loop
    for context, target in tqdm(sampled_pairs, desc="Evaluating LSTM"):
        # Normalise the context string but PRESERVE the trailing space!
        norm_context = normalise_arabic(context)
        if context.endswith(" "):
            norm_context += " "

        norm_target = normalise_arabic(target)

        predictions = neural_model.predict_next_word_beam(norm_context, top_k=5)
        pred_words = [word for word, score in predictions]

        if len(pred_words) >= 1 and pred_words[0] == norm_target:
            top_1 += 1
        if norm_target in pred_words[:3]:
            top_3 += 1
        if norm_target in pred_words[:5]:
            top_5 += 1

    # Calculate Percentages
    acc_1 = top_1 / len(sampled_pairs)
    acc_3 = top_3 / len(sampled_pairs)
    acc_5 = top_5 / len(sampled_pairs)

    print("\n--- LSTM Full-Word Evaluation Results ---")
    print(f"Top-1 Word Accuracy: {acc_1:.2%}")
    print(f"Top-3 Word Accuracy: {acc_3:.2%}")
    print(f"Top-5 Word Accuracy: {acc_5:.2%}")

    # Save Report
    report_dir = "artifacts/nws/evaluation/nwp"
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "lstm_report.json")

    report = {
        "samples_evaluated": len(sampled_pairs),
        "top_1_accuracy": acc_1,
        "top_3_accuracy": acc_3,
        "top_5_accuracy": acc_5,
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    print(f"Report saved to {report_path}")


if __name__ == "__main__":
    run_lstm_evaluation(num_samples=2500)
