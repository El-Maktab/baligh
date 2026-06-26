"""Hybrid Arabic Next-Word Predictor.

A hybrid approach that uses the lstm model along with the word n-gram
model to give a balanced prediction.

Authors:
    - Akram Hany
"""

import math

from src.services.nws.features.nwp.lstm.model import (
    LSTMNWPModel,
)
from src.services.nws.features.nwp.word_ngram.model import WordNGramLM


class HybridArabicPredictor:
    """A hybrid model combining LSTM and N-Gram predictions."""

    def __init__(self, neural_model: LSTMNWPModel, kn_model: WordNGramLM):
        """Initializes the HybridArabicPredictor.

        Args:
            neural_model: The pre-trained LSTM predictor.
            kn_model: The pre-trained Kneser-Ney Word N-Gram language model.
        """
        self.neural = neural_model
        self.kn = kn_model

    def predict(self, context_text: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Predicts the top-k next words using Confidence-Weighted mix.

        Args:
            context_text: The normalized Arabic text preceding the cursor.
            top_k: The number of top suggestions to return.

        Returns:
            A list of tuples containing (word, normalized_probability_score) sorted
            in descending order of combined probability.
        """
        if not context_text.strip():
            return []

        # Run the LSTM Autoregressive Beam Search to extract top-K full words
        neural_results = self.neural.predict_next_word_beam(
            context_text, top_k=top_k * 2
        )

        neural_log_probs = {}
        for word, score in neural_results:
            neural_log_probs[word] = score

        if neural_log_probs:
            max_neural_log_prob = max(neural_log_probs.values())
        else:
            max_neural_log_prob = -float("inf")

        # get the n-gram results
        context_tokens = context_text.strip().split()
        kn_candidates = self.kn.predict_next(context_tokens, top_k=top_k * 2)

        kn_scores = {}
        for word in kn_candidates:
            log_p = self.kn.score_token(context_tokens, word)
            kn_scores[word] = log_p

        # Compute the confidence
        if max_neural_log_prob > math.log(0.35):
            alpha = 0.75
        else:
            alpha = 0.50

        # Merge the two candidate lists and sum weighted log-probabilities
        combined_scores = {}
        all_words = set(list(neural_log_probs.keys()) + list(kn_scores.keys()))

        for word in all_words:
            if word in neural_log_probs:
                log_n = neural_log_probs[word]
            else:
                log_n = -20.0  # Heavy penalty for unseen words

            if word in kn_scores:
                log_kn = kn_scores[word]
            else:
                # Score the word if it wasn't even suggested by kn model
                log_kn = self.kn.score_token(context_tokens, word)

            # formula for merging the 2 models
            final_score = (alpha * log_n) + ((1.0 - alpha) * log_kn)
            combined_scores[word] = final_score

        # Return the top-5 words sorted by combined score
        top_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[
            :top_k
        ]

        if not top_results:
            return []

        # normalize results
        max_score = top_results[0][1]
        exp_scores = [math.exp(score - max_score) for _, score in top_results]
        sum_exp = sum(exp_scores)

        normalized_results = []
        for (word, _), exp_s in zip(top_results, exp_scores, strict=True):
            normalized_results.append((word, exp_s / sum_exp))

        return normalized_results
