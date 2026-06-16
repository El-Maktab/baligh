import torch
from torch.utils.data import DataLoader
    
class GECCollator:

    def __init__(
        self,
        pad_token_id: int,
        label_pad_id: int = -100,
    ):
        self.pad_token_id = pad_token_id
        self.label_pad_id = label_pad_id

    def __call__(self, batch):

        max_len = max(
            len(item["input_ids"])
            for item in batch
        )

        input_ids = []
        attention_masks = []
        labels = []

        for item in batch:

            seq_len = len(item["input_ids"])
            pad_len = max_len - seq_len

            input_ids.append(
                item["input_ids"]
                + [self.pad_token_id] * pad_len
            )

            if "attention_mask" in item:
                attention_masks.append(
                    item["attention_mask"]
                    + [0] * pad_len
                )
            else:
                attention_masks.append(
                    [1] * seq_len
                    + [0] * pad_len
                )

            labels.append(
                item["label_ids"]
                + [self.label_pad_id] * pad_len
            )

        return {
            "input_ids": torch.tensor(
                input_ids,
                dtype=torch.long,
            ),
            "attention_mask": torch.tensor(
                attention_masks,
                dtype=torch.long,
            ),
            "labels": torch.tensor(
                labels,
                dtype=torch.long,
            ),
        }


def create_dataloader(
    dataset,
    batch_size,
    shuffle,
    tokenizer,
):

    collator = GECCollator(
        pad_token_id=tokenizer.pad_token_id,
    )

    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        collate_fn=collator,
    )