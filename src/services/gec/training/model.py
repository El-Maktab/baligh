from transformers import AutoModelForTokenClassification


def create_model(checkpoint, label2id):
    id2label = {v: k for k, v in label2id.items()}
    return AutoModelForTokenClassification.from_pretrained(
        checkpoint,
        num_labels=len(label2id),
        id2label=id2label,
        label2id=label2id,
    )
