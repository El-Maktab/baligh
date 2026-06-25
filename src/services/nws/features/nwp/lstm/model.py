import math

import sentencepiece as spm
import torch
import torch.nn as nn

PAD_ID = 0
UNK_ID = 1
BOS_ID = 2
EOS_ID = 3


class ArabicLSTMLM(nn.Module):
    """2-layer LSTM Language Model for Arabic autocomplete.
    Architecture: Embedding -> Dropout -> LSTM -> Dropout -> Linear (tied weights)
    """

    def __init__(
        self,
        vocab_size: int,
        embed_dim: int,
        hidden_size: int,
        num_layers: int,
        dropout: float,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.embed_dim = embed_dim

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

    def forward(
        self, input_ids: torch.Tensor, hidden: tuple | None = None
    ) -> tuple[torch.Tensor, tuple]:
        x = self.drop(self.embedding(input_ids))
        x, hidden = self.lstm(x, hidden)
        x = self.drop(x)
        if self.pre_output_proj is not None:
            x = self.pre_output_proj(x)
        logits = self.output_proj(x)
        return logits, hidden

    def init_hidden(self, batch_size: int) -> tuple[torch.Tensor, torch.Tensor]:
        h = torch.zeros(
            self.num_layers,
            batch_size,
            self.hidden_size,
            device=next(self.parameters()).device,
        )
        c = torch.zeros_like(h)
        return (h, c)


class LSTMNWPModel:
    """Wrapper that conforms to the WordNGramLM protocol."""

    def __init__(self, model_path: str, sp_model_path: str, device: str = "cpu"):
        self.device = torch.device(device)
        self.sp = spm.SentencePieceProcessor(model_file=sp_model_path)

        self.model = ArabicLSTMLM(
            vocab_size=12000, embed_dim=256, hidden_size=512, num_layers=2, dropout=0.0
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
            loss_fn = nn.CrossEntropyLoss(reduction="mean", ignore_index=PAD_ID)
            loss = loss_fn(logits.view(-1, self.sp.vocab_size()), y.view(-1))

        return (
            -loss.item()
        )  # score_sequence returns positive log_prob, loss is negative log_prob

    def predict_next_word_beam(
        self, text: str, top_k: int = 5, beam_width: int = 10
    ) -> list[tuple[str, float]]:
        """Predict the top-k next words using autoregressive beam search."""
        import re

        ARABIC_CHARS = re.compile(r"[\u0600-\u06FF\u0750-\u077F]")

        ctx_ids_list = self.sp.encode(text, out_type=int)[-32:]
        if not ctx_ids_list:
            return []

        ctx_ids = torch.tensor([ctx_ids_list], dtype=torch.long, device=self.device)

        # Each beam: (cumulative_log_prob, token_ids_generated_so_far)
        beams: list[tuple[float, list[int]]] = [(0.0, [])]
        completed = []  # (score, word_string)

        for step in range(8):  # max tokens per word
            all_candidates = []

            for cum_score, token_ids in beams:
                # Build context with tokens generated so far
                if token_ids:
                    extension = torch.tensor([token_ids], device=self.device)
                    new_ctx = torch.cat([ctx_ids, extension], dim=1)
                else:
                    new_ctx = ctx_ids

                with torch.no_grad():
                    logits, _ = self.model(new_ctx)
                    probs = torch.softmax(logits[0, -1, :], dim=-1)

                top_probs, top_ids = torch.topk(probs, k=beam_width)

                for prob, tid in zip(top_probs.tolist(), top_ids.tolist()):
                    if tid in (PAD_ID, UNK_ID, BOS_ID):
                        continue

                    piece = self.sp.id_to_piece(tid)
                    new_token_ids = token_ids + [tid]
                    # Length-normalized cumulative score
                    new_score = (cum_score + math.log(prob + 1e-10)) / len(
                        new_token_ids
                    )

                    # If next piece starts a new word → current sequence is complete
                    if step > 0 and (piece.startswith("\u2581") or tid == EOS_ID):
                        decoded = self.sp.decode(token_ids).strip()
                        if decoded and ARABIC_CHARS.search(decoded):
                            completed.append((new_score, decoded))
                    else:
                        all_candidates.append((new_score, new_token_ids))

            if not all_candidates:
                break

            # Global pruning — all beams compete together
            beams = sorted(all_candidates, key=lambda x: x[0], reverse=True)[
                :beam_width
            ]

            if len(completed) >= top_k * 3:
                break

        # Deduplicate and return top-k unique words
        seen = {}
        for score, word in sorted(completed, reverse=True):
            if word not in seen:
                seen[word] = score
            if len(seen) >= top_k:
                break

        return [(word, score) for word, score in seen.items()]
