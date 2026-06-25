import json

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