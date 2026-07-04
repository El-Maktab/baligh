"""GED evaluation datasets.

We test on:
- QALB14
- QALB15 L1 (L1 is for native speakers, L2 is for non-native speakers)
- QALB15 L2
- ZAEBUC

Author:
  Amir Anwar
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from src.runtime_config import REPO_ROOT

NO_ERROR = "UC"
UNKNOWN = "UNK"

LABEL_TO_CATEGORY = {
    "UC": NO_ERROR,
    "REPLACE_O": "OT",
    "REPLACE_P": "PC",
    "REPLACE_M": "MO",
    "REPLACE_S": "SY",
    "MERGE-B": "MG",
    "MERGE-I": "MG",
    "SPLIT": "SP",
    "DELETE": UNKNOWN,
    "REPLACE_X": UNKNOWN,
    "UNK": UNKNOWN,
    "REPLACE_M+REPLACE_O": "MO",
    "REPLACE_O+REPLACE_X": "OT",
}


class DatasetError(ValueError):
    """Raised when an evaluation corpus violates contract."""


@dataclass(frozen=True)
class DatasetSpec:
    """Dataset loc and name."""

    name: str
    path: Path
    sha256: str


@dataclass(frozen=True)
class GoldSentence:
    """One pretokenized gold sentence."""

    tokens: tuple[str, ...]
    labels: tuple[str, ...]


_DATA_ROOT = REPO_ROOT / "src" / "services" / "ged" / "data" / "evaluation"
DATASETS = {
    "qalb14": DatasetSpec(
        "qalb14",
        _DATA_ROOT / "qalb14" / "test.txt",
        "f2303ae36d819cd6abb5e1a7a227c4b5c22d56aaa3a330a177f7c97f81be6812",
    ),
    "qalb15_l1": DatasetSpec(
        "qalb15_l1",
        _DATA_ROOT / "qalb15_l1" / "test.txt",
        "2f91d49d2fb66437510e107dfde69df6ac6b1c6bca0b05f94a2a9d09af2fd130",
    ),
    "qalb15_l2": DatasetSpec(
        "qalb15_l2",
        _DATA_ROOT / "qalb15_l2" / "test.txt",
        "531ad0d5be5215727bc218d985996a14762de7290a8fcb18daca5dc1756e22f1",
    ),
    "zaebuc": DatasetSpec(
        "zaebuc",
        _DATA_ROOT / "zaebuc" / "test.txt",
        "37b1d620384cac1c0f07d186bc6f55ae47150ec93b18917463b3b7b3b8bf78dc",
    ),
}


def file_sha256(path: Path) -> str:
    """Calculate a file digest without loading the whole corpus."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_dataset(spec: DatasetSpec, limit: int | None = None) -> list[GoldSentence]:
    """Read a dataset with QALB-like format."""
    if not spec.path.is_file():
        raise DatasetError(f"Dataset {spec.name!r} is missing: {spec.path}")

    actual_digest = file_sha256(spec.path)
    if actual_digest != spec.sha256:
        raise DatasetError(
            f"Checksum mismatch for {spec.name}: expected {spec.sha256}, "
            f"got {actual_digest}."
        )

    sentences: list[GoldSentence] = []
    tokens: list[str] = []
    labels: list[str] = []

    for line_number, line in enumerate(
        spec.path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line:
            if tokens:
                sentences.append(GoldSentence(tuple(tokens), tuple(labels)))
                tokens, labels = [], []
                if limit is not None and len(sentences) >= limit:
                    break
            continue

        fields = line.split("\t")
        if len(fields) != 2 or not fields[0]:
            raise DatasetError(f"{spec.name}:{line_number}: expected TOKEN<TAB>LABEL.")
        token, raw_label = fields
        try:
            label = LABEL_TO_CATEGORY[raw_label]
        except KeyError as error:
            raise DatasetError(
                f"{spec.name}:{line_number}: unknown label {raw_label!r}."
            ) from error
        tokens.append(token)
        labels.append(label)

    if tokens and (limit is None or len(sentences) < limit):
        sentences.append(GoldSentence(tuple(tokens), tuple(labels)))
    if not sentences:
        raise DatasetError(f"Dataset {spec.name!r} contains no sentences.")
    return sentences
