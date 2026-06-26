import math

from src.services.nws.features.nwp.lstm.model import (
    LSTMNWPModel,
)
from src.services.nws.features.nwp.word_ngram.model import WordNGramLM


class HybridArabicPredictor:
    def __init__(self, neural_model: LSTMNWPModel, kn_model: WordNGramLM):
        self.neural = neural_model
        self.kn = kn_model

    def predict(self, context_text: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Predicts the top-k next words using Confidence-Weighted Blending."""
        # 1. Take the last N characters (where N covers ~32 subword tokens)
        # SentencePiece handles the text internally
        context_ids = self.neural.sp.encode(context_text, out_type=int)[-32:]
        if not context_ids:
            return []

        # 2. Run the LSTM Autoregressive Beam Search to extract top-K full words
        neural_results = self.neural.predict_next_word_beam(
            context_text, top_k=top_k * 2
        )

        neural_candidates = {}
        for word, score in neural_results:
            # Convert length-normalized log probability back to raw probability for blending
            neural_candidates[word] = math.exp(score)

        # The max_neural_prob is used for alpha blending scaling. We use the top word's prob
        if neural_candidates:
            max_neural_prob = max(neural_candidates.values())
        else:
            max_neural_prob = 0.0

        # 4. Query the Kneser-Ney model with the last 2 full words
        # Clean the context to match the N-Gram dictionary format
        context_tokens = context_text.strip().split()
        kn_candidates = self.kn.predict_next(context_tokens, top_k=top_k * 2)

        kn_scores = {}
        for word in kn_candidates:
            # Re-calculate the exact Kneser-Ney probability for blending
            # score_token returns log_prob, so we exp() it to get raw probability or use log-space directly
            log_p = self.kn.score_token(context_tokens, word)
            kn_scores[word] = log_p

        # 5. Compute the confidence of the neural model
        if max_neural_prob > 0.35:
            alpha = 0.75
        else:
            alpha = 0.50

        # 6. Merge the two candidate lists and sum weighted log-probabilities
        combined_scores = {}
        all_words = set(list(neural_candidates.keys()) + list(kn_scores.keys()))

        for word in all_words:
            # Get neural log_prob
            if word in neural_candidates:
                p_n = max(neural_candidates[word], 1e-10)
                log_n = math.log(p_n)
            else:
                log_n = -10.0  # Heavy penalty for unseen

            # Get KN log_prob
            if word in kn_scores:
                log_kn = kn_scores[word]
            else:
                # Ask KN model to score it even if it wasn't in its top-k
                log_kn = self.kn.score_token(context_tokens, word)

            # Confidence-Weighted Blending Formula
            final_score = (alpha * log_n) + ((1.0 - alpha) * log_kn)
            combined_scores[word] = final_score

        # Return the top-5 words sorted by combined score
        top_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[
            :top_k
        ]

        if not top_results:
            return []

        # Softmax normalization over the top-K candidates
        max_score = top_results[0][1]
        exp_scores = [math.exp(score - max_score) for _, score in top_results]
        sum_exp = sum(exp_scores)

        normalized_results = []
        for (word, _), exp_s in zip(top_results, exp_scores, strict=True):
            normalized_results.append((word, exp_s / sum_exp))

        return normalized_results
