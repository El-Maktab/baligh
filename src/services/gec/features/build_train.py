"""Build and export the GEC training dataset from raw parallel corpora."""

import json
from pathlib import Path

from src.services.gec.config import (
    TRAIN_COR_PATH,
    TRAIN_SENT_PATH,
    MIN_LABEL_FREQUENCY,
    LABEL2ID_PATH,
    ID2LABEL_PATH,
    CHECKPOINT_PATH,
)
from src.services.gec.features.vocabulary import LabelVocabularyBuilder
from src.services.gec.features.common import build_feature_builder
from src.services.gec.features.feature_builder import FeatureBuilder
from src.services.gec.features.pruner import LabelPruner
from src.services.gec.features.exporter import DatasetExporter


def save_json(
    data: dict,
    output_path: Path,
) -> None:
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_train() -> None:
    builder: FeatureBuilder = build_feature_builder()

    examples = builder.build_pipeline(
        TRAIN_SENT_PATH,
        TRAIN_COR_PATH,
        CHECKPOINT_PATH,
    )
    print("examples created")

    pruner = LabelPruner(min_frequency=MIN_LABEL_FREQUENCY)

    examples = pruner.prune(examples)
    print("pruned")
    vocab_builder = LabelVocabularyBuilder()

    label2id, id2label = vocab_builder.build(examples)

    save_json(label2id, LABEL2ID_PATH)
    save_json(id2label, ID2LABEL_PATH)

    print("label2id created")
    # exporter = DatasetExporter()
    # exporter.export_jsonl(examples, NOPNX_TRAIN_OUTPUT)
    # exporter.export_jsonl(examples, PNX_TRAIN_OUTPUT)

