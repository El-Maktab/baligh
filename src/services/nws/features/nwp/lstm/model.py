import math
import torch
import torch.nn as nn
import sentencepiece as spm
from typing import List, Tuple, Optional

PAD_ID = 0
UNK_ID = 1
BOS_ID = 2
EOS_ID = 3

class ArabicLSTMLM(nn.Module):
    """
    2-layer LSTM Language Model for Arabic autocomplete.
    Architecture: Embedding -> Dropout -> LSTM -> Dropout -> Linear (tied weights)
    """
    def __init__(self, vocab_size: int, embed_dim: int,
                 hidden_size: int, num_layers: int, dropout: float):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers  = num_layers
        self.embed_dim   = embed_dim

        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=PAD_ID)
        nn.init.uniform_(self.embedding.weight, -0.1, 0.1)
        self.embedding.weight.data[PAD_ID].fill_(0)

        self.lstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0.0,
            batch_first=True,
        )

        self.output_proj = nn.Linear(hidden_size, vocab_size, bias=False)

        # Weight tying
        if embed_dim == hidden_size:
            self.output_proj.weight = self.embedding.weight
            self.pre_output_proj = None
        else:
            self.pre_output_proj = nn.Linear(hidden_size, embed_dim, bias=False)
            self.output_proj.weight = self.embedding.weight

        self.drop = nn.Dropout(dropout)

    def forward(self, input_ids: torch.Tensor,
                hidden: Optional[Tuple] = None) -> Tuple[torch.Tensor, Tuple]:
        x = self.drop(self.embedding(input_ids))
        x, hidden = self.lstm(x, hidden)
        x = self.drop(x)
        if self.pre_output_proj is not None:
            x = self.pre_output_proj(x)
        logits = self.output_proj(x)
        return logits, hidden

    def init_hidden(self, batch_size: int) -> Tuple[torch.Tensor, torch.Tensor]:
        h = torch.zeros(self.num_layers, batch_size, self.hidden_size,
                        device=next(self.parameters()).device)
        c = torch.zeros_like(h)
        return (h, c)


class LSTMNWPModel:
    """Wrapper that conforms to the WordNGramLM protocol."""
    
    def __init__(self, model_path: str, sp_model_path: str, device: str = "cpu"):
        self.device = torch.device(device)
        self.sp = spm.SentencePieceProcessor(model_file=sp_model_path)
        
        self.model = ArabicLSTMLM(
            vocab_size=12000,
            embed_dim=256,
            hidden_size=512,
            num_layers=2,
            dropout=0.0
        )
        ckpt = torch.load(model_path, map_location=self.device, weights_only=False)
        if "model_state_dict" in ckpt:
            self.model.load_state_dict(ckpt["model_state_dict"])
        else:
            self.model.load_state_dict(ckpt)
            
        self.model.to(self.device)
        self.model.eval()

    def score_sequence(self, tokens: list[str]) -> float:
        """Calculate the average log-probability of a sequence for perplexity."""
        if not tokens:
            return 0.0
        
        # Join tokens back into a single string to let SentencePiece encode it naturally
        text = " ".join(tokens)
        ids = self.sp.encode(text, out_type=int)
        if len(ids) < 2:
            return 0.0
            
        with torch.no_grad():
            x = torch.tensor([ids[:-1]], dtype=torch.long, device=self.device)
            y = torch.tensor([ids[1:]], dtype=torch.long, device=self.device)
            
            logits, _ = self.model(x)
            
            # Use CrossEntropyLoss to compute the exact NLL loss
            loss_fn = nn.CrossEntropyLoss(reduction='mean', ignore_index=PAD_ID)
            loss = loss_fn(logits.view(-1, self.sp.vocab_size()), y.view(-1))
            
        return -loss.item()  # score_sequence returns positive log_prob, loss is negative log_prob

    def predict_next(self, context_tokens: list[str], top_k: int = 5, debug: bool = False) -> list[str]:
        """Predict the top-k next words (used by evaluator or standalone).
        Note: The true Hybrid Predictor will handle the subword decoding logic internally.
        This is a fallback baseline subword decoding.
        """
        context_text = " ".join(context_tokens)
        context_ids = self.sp.encode(context_text, out_type=int)[-32:]
        if not context_ids:
            return []
            
        with torch.no_grad():
            x = torch.tensor([context_ids], dtype=torch.long, device=self.device)
            logits, _ = self.model(x)
            
            next_token_logits = logits[0, -1, :]
            probs = torch.softmax(next_token_logits, dim=-1)
            
            top_probs, top_indices = torch.topk(probs, k=top_k*2)
            
        results = []
        for idx in top_indices:
            idx_val = idx.item()
            if idx_val in (PAD_ID, UNK_ID, BOS_ID, EOS_ID):
                continue
            word = self.sp.decode([idx_val])
            if word and word not in results:
                results.append(word)
                if len(results) >= top_k:
                    break
        return results
