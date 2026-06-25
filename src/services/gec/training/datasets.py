import json
from pathlib import Path

import torch
from torch.utils.data import Dataset


class GECTrainingDataset(Dataset):

    def __init__(self, jsonl_path, tokenizer, label2id, max_length=256):
        self.tokenizer = tokenizer
        self.label2id = label2id
        self.max_length = max_length
        self.unk_label_id = label2id.get("[UNK_EDIT]", 1)
        self.examples = []
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self.examples.append(json.loads(line))

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        example = self.examples[idx]
        subwords = example.get("subwords", example.get("tokens", []))
        labels_raw = example.get("labels_star", example.get("labels", []))

        label_ids = [
            self.label2id.get(l, self.unk_label_id) for l in labels_raw
        ]

        # Convert pre-projected subwords directly to IDs — do NOT retokenize
        # with is_split_into_words=True, which would re-split already-split
        # subword strings (e.g. "##ثو") and corrupt both token sequences and
        # label alignment.
        token_ids = self.tokenizer.convert_tokens_to_ids(subwords)

        # Truncate to max_length minus 2 to leave room for [CLS] and [SEP]
        max_content = self.max_length - 2
        token_ids = token_ids[:max_content]
        label_ids = label_ids[:max_content]

        token_ids = [self.tokenizer.cls_token_id] + token_ids + [self.tokenizer.sep_token_id]
        label_ids = [-100] + label_ids + [-100]

        seq_len = len(token_ids)
        pad_len = self.max_length - seq_len
        attention_mask = [1] * seq_len + [0] * pad_len
        if pad_len > 0:
            token_ids = token_ids + [self.tokenizer.pad_token_id] * pad_len

        return {
            "input_ids": token_ids,
            "attention_mask": attention_mask,
            "labels": label_ids,
        }
