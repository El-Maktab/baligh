"""Corpus paths and raw sentence parsing for GED ML training."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from src.services.ged.config import GED_ROOT

FORBIDDEN_SUBSTRINGS = ("&gt;", "&lt;", ">", "<")
DATA_ROOT = GED_ROOT / "data" / "ml"


@dataclass(frozen=True)
class RawSentence:
    """One token-label sequence from a GED corpus."""

    tokens: tuple[str, ...]
    raw_labels: tuple[str, ...]


def dataset_dir(name: str) -> Path:
    """Return the local dataset directory for a training corpus."""
    path = DATA_ROOT / name / "data"
    if not path.is_dir():
        raise FileNotFoundError(f"Training dataset {name!r} is missing: {path}")
    return path


def read_labeled_sentences(path: Path) -> list[RawSentence]:
    """Read a sentence-separated TOKEN<TAB>LABEL corpus."""
    sentences: list[RawSentence] = []
    tokens: list[str] = []
    labels: list[str] = []

    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line:
            if tokens:
                sentences.append(RawSentence(tuple(tokens), tuple(labels)))
                tokens, labels = [], []
            continue

        fields = line.split("\t")
        if len(fields) != 2:
            raise ValueError(f"{path}:{line_number}: expected TOKEN<TAB>LABEL.")
        token, label = fields
        tokens.append(token)
        labels.append(label)

    if tokens:
        sentences.append(RawSentence(tuple(tokens), tuple(labels)))
    return sentences


def contains_forbidden_symbol(tokens: Sequence[str]) -> bool:
    """Return whether a raw token sequence contains unsupported markup symbols."""
    return any(
        any(symbol in token for symbol in FORBIDDEN_SUBSTRINGS) for token in tokens
    )
