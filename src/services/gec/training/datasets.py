"""PyTorch Dataset for loading GEC edit-tagging training examples from JSONL."""

import json
from pathlib import Path

from torch.utils.data import Dataset


class GECTrainingDataset(Dataset):
    """Loads pre-processed token/label JSONL files for GEC training.

    Each JSONL line is expected to have a ``subwords`` (or ``tokens``) key
    holding a list of subword-token strings and a ``labels`` key holding a
    list of compressed edit-tag strings.

    The dataset converts subword strings to integer ``input_ids`` via the
    provided HuggingFace tokenizer and maps string labels to integer
    ``label_ids`` using the ``label2id`` vocabulary.
    """

    def __init__(
        self,
        jsonl_path: Path,
        tokenizer,
        label2id: dict[str, int],
        max_length: int = 512,
    ) -> None:
        self.jsonl_path = Path(jsonl_path)
        self.tokenizer = tokenizer
        self.label2id = label2id
        self.max_length = max_length
        self.unk_label_id: int = label2id.get("[UNK_EDIT]", 1)
        self.examples: list[dict] = self._load_examples()

    def _load_examples(self) -> list[dict]:
        examples: list[dict] = []
        with self.jsonl_path.open(encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                examples.append(json.loads(stripped))
        return examples

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> dict[str, list[int]]:
        example = self.examples[idx]

        subwords = example.get("subwords", example.get("tokens", []))

        labels_raw: list[str] = example.get("labels_star", example.get("labels", []))

        label_ids: list[int] = [
            self.label2id.get(label, self.unk_label_id)
            for label in labels_raw
        ]

        encoding = self.tokenizer(
            subwords,
            is_split_into_words=True,
            add_special_tokens=True,
            max_length=self.max_length,
            truncation=True,
            padding=False,
        )

        input_ids: list[int] = encoding["input_ids"]
        attention_mask: list[int] = encoding["attention_mask"]

        word_ids = encoding.word_ids()
        
        aligned_labels = []
        for token_idx, word_idx in enumerate(word_ids):
            if word_idx is None:
                aligned_labels.append(-100)
            else:
                if word_idx < len(label_ids):
                    aligned_labels.append(label_ids[word_idx])
                else:
                    aligned_labels.append(-100)

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": aligned_labels,
        }
