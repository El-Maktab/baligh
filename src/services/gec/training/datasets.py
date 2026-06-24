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

        encoding = self.tokenizer(
            subwords,
            is_split_into_words=True,
            add_special_tokens=True,
            max_length=self.max_length,
            truncation=True,
            padding=False,
        )

        word_ids = encoding.word_ids()
        aligned_labels = []
        for word_idx in word_ids:
            if word_idx is None:
                aligned_labels.append(-100)
            elif word_idx < len(label_ids):
                aligned_labels.append(label_ids[word_idx])
            else:
                aligned_labels.append(-100)

        return {
            "input_ids": encoding["input_ids"],
            "attention_mask": encoding["attention_mask"],
            "labels": aligned_labels,
        }
