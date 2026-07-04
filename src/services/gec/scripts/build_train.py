"""Build and export the GEC training dataset from raw parallel corpora."""

import json
from pathlib import Path

from loguru import logger

from src.runtime_config import load_runtime_config
from src.services.gec.features.common import build_feature_builder
from src.services.gec.features.exporter import DatasetExporter
from src.services.gec.features.feature_builder import FeatureBuilder
from src.services.gec.features.pruner import LabelPruner
from src.services.gec.features.vocabulary import LabelVocabularyBuilder
from src.services.gec.modules.edit_tagger.preprocessing.segregator import Segregator

_EDIT_TAGGER = load_runtime_config().gec.edit_tagger
CHECKPOINT_PATH = _EDIT_TAGGER.resolved_checkpoint_path
ID2LABEL_PATH = _EDIT_TAGGER.resolved_id2label_path
LABEL2ID_PATH = _EDIT_TAGGER.resolved_label2id_path
MIN_LABEL_FREQUENCY = _EDIT_TAGGER.min_label_frequency
NOPNX_TRAIN_OUTPUT = _EDIT_TAGGER.resolved_nopnx_train_output
PNX_TRAIN_OUTPUT = _EDIT_TAGGER.resolved_pnx_train_output
TRAIN_COR_PATH = _EDIT_TAGGER.resolved_train_cor_path
TRAIN_SENT_PATH = _EDIT_TAGGER.resolved_train_sent_path


def save_json(
    data: dict,
    output_path: Path,
) -> None:
    """Write a dictionary to a JSON file with pretty-printing."""
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_train() -> None:
    """Build and export the GEC training dataset from raw parallel corpora."""
    builder: FeatureBuilder = build_feature_builder()

    examples = builder.build_pipeline(
        TRAIN_SENT_PATH,
        TRAIN_COR_PATH,
        CHECKPOINT_PATH,
    )
    logger.info("examples created")

    pruner = LabelPruner(min_frequency=MIN_LABEL_FREQUENCY)

    examples = pruner.prune(examples)
    logger.info("pruned")
    vocab_builder = LabelVocabularyBuilder()

    label2id, id2label = vocab_builder.build(examples)

    save_json(label2id, LABEL2ID_PATH)
    save_json(id2label, ID2LABEL_PATH)

    logger.info("label2id created")

    exporter = DatasetExporter()
    segregator = Segregator()
    punc_examples, non_punc_examples = segregator.segregate(examples)
    exporter.export_jsonl(punc_examples, NOPNX_TRAIN_OUTPUT)
    exporter.export_jsonl(non_punc_examples, PNX_TRAIN_OUTPUT)
