"""GEC training dataset for token classification."""

import json

from torch.utils.data import Dataset


class GECTrainingDataset(Dataset):
    """PyTorch dataset that loads GEC training examples from a JSONL file."""

    def __init__(self, jsonl_path, tokenizer, label2id, max_length=256):
        """Initialize the dataset from a JSONL file."""
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
        """Return the number of examples."""
        return len(self.examples)

    def __getitem__(self, idx):
        """Return a single training example as a feature dict."""
        example = self.examples[idx]
        subwords = example.get("subwords", example.get("tokens", []))
        labels_raw = example.get("labels_star", example.get("labels", []))

        label_ids = [self.label2id.get(lbl, self.unk_label_id) for lbl in labels_raw]

        max_content = self.max_length - 2
        subwords = subwords[:max_content]
        label_ids = label_ids[:max_content]

        token_ids = self.tokenizer.convert_tokens_to_ids(subwords)
        input_ids = (
            [self.tokenizer.cls_token_id] + token_ids + [self.tokenizer.sep_token_id]
        )
        attention_mask = [1] * len(input_ids)

        aligned_labels = [-100] + label_ids + [-100]

        padding_len = self.max_length - len(input_ids)
        if padding_len > 0:
            input_ids += [self.tokenizer.pad_token_id] * padding_len
            attention_mask += [0] * padding_len
            aligned_labels += [-100] * padding_len

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": aligned_labels,
        }
