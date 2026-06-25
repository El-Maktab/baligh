import math
import torch
from typing import List, Tuple

from src.services.nws.features.nwp.word_ngram.model import WordNGramLM
from src.services.nws.features.nwp.lstm.model import LSTMNWPModel, PAD_ID, UNK_ID, BOS_ID, EOS_ID

class HybridArabicPredictor:
    def __init__(self, neural_model: LSTMNWPModel, kn_model: WordNGramLM):
        self.neural = neural_model
        self.kn = kn_model

    def predict(self, context_text: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Predicts the top-k next words using Confidence-Weighted Blending.
        """
        # 1. Take the last N characters (where N covers ~32 subword tokens)
        # SentencePiece handles the text internally
        context_ids = self.neural.sp.encode(context_text, out_type=int)[-32:]
        if not context_ids:
            return []

        # 2. Run a forward pass through the LSTM
        with torch.no_grad():
            x = torch.tensor([context_ids], dtype=torch.long, device=self.neural.device)
            logits, _ = self.neural.model(x)
            
            next_token_logits = logits[0, -1, :]
            probs = torch.softmax(next_token_logits, dim=-1)

        # Extract top candidates from neural
        top_neural_probs, top_neural_indices = torch.topk(probs, k=top_k * 5)
        
        neural_candidates = {}
        max_neural_prob = top_neural_probs[0].item()

        # 3. Decode the top-K subword candidates back to full words
        for p, idx in zip(top_neural_probs, top_neural_indices):
            idx_val = idx.item()
            if idx_val in (PAD_ID, UNK_ID, BOS_ID, EOS_ID):
                continue
                
            prob = p.item()
            
            # Decode the context plus this new token to handle subword boundaries correctly
            decoded_full = self.neural.sp.decode(context_ids + [idx_val])
            words = decoded_full.split()
            if not words:
                continue
            word = words[-1].strip()
            
            if word:
                if word not in neural_candidates:
                    neural_candidates[word] = prob
                else:
                    neural_candidates[word] += prob

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
        top_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # Strip out the scores if we just want the words, but returning tuples is better for evaluation
        return top_results
