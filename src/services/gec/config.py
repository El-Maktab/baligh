from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = ROOT / "services" / "gec" / "data" / "edit_tagger" / "raw"
PROCESSED_DATA_DIR = ROOT / "services" / "gec" / "data" / "edit_tagger" / "processed"

CHECKPOINT_PATH = PROCESSED_DATA_DIR / "tokens_labels.jsonl"
TRAIN_SENT_PATH = RAW_DATA_DIR / "train" / "QALB-2014-L1-Train.sent"
TRAIN_COR_PATH = RAW_DATA_DIR / "train" / "QALB-2014-L1-Train.cor"

LABEL2ID_PATH = PROCESSED_DATA_DIR / "label2id.json"
ID2LABEL_PATH = PROCESSED_DATA_DIR / "id2label.json"

NOPNX_TRAIN_OUTPUT = PROCESSED_DATA_DIR / "qalb14_nopnx_train.jsonl"
PNX_TRAIN_OUTPUT = PROCESSED_DATA_DIR / "qalb14_pnx_train.jsonl"

MIN_LABEL_FREQUENCY = 3
DEFAULT_LABEL = "KEEP"
UNK_LABEL = "[UNK_EDIT]"
PAD_LABEL = "[PAD]"

# CRF Configuration
USE_CRF = False  # Set to True to enable CRF layer
CRF_CHECKPOINT_SUFFIX = "_crf"  # Suffix for checkpoint directories when CRF is used