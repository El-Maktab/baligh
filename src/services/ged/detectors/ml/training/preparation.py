"""Prepare GED ML corpora with Baligh preprocessing alignment."""

from __future__ import annotations

import contextlib
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib

from src.services.ged.detectors.ml.features import (
    FEATURE_SET_VERSION,
    sentence_features,
)
from src.services.ged.detectors.ml.training.corpus import (
    RawSentence,
    contains_forbidden_symbol,
    dataset_dir,
    read_labeled_sentences,
)
from src.services.ged.detectors.ml.training.logging import format_seconds, log
from src.services.ged.evaluation.datasets import LABEL_TO_CATEGORY
from src.services.preprocessing import PreprocessingInput, preprocess


@dataclass(frozen=True)
class PreparedSentence:
    """A training or development sentence after Baligh preprocessing."""

    features: list[dict[str, object]]
    labels: list[str]


@dataclass(frozen=True)
class PreparationStats:
    """Preparation counters for one split."""

    total_sentences: int
    kept_sentences: int
    discarded_forbidden_sentences: int
    discarded_mismatch_sentences: int
    total_tokens: int
    kept_tokens: int

    def as_dict(self) -> dict[str, int]:
        """Return JSON-friendly counters."""
        return {
            "total_sentences": self.total_sentences,
            "kept_sentences": self.kept_sentences,
            "discarded_forbidden_sentences": self.discarded_forbidden_sentences,
            "discarded_mismatch_sentences": self.discarded_mismatch_sentences,
            "total_tokens": self.total_tokens,
            "kept_tokens": self.kept_tokens,
        }


def prepare_sentences(
    sentences: Sequence[RawSentence],
) -> tuple[list[PreparedSentence], PreparationStats]:
    """Keep only sentences that align exactly with Baligh preprocessing."""
    started_at = time.perf_counter()
    prepared: list[PreparedSentence] = []
    discarded_forbidden = 0
    discarded_mismatch = 0
    total_tokens = 0
    kept_tokens = 0

    for index, sentence in enumerate(sentences, start=1):
        if index % 250 == 0:
            log(
                f"prepared {index}/{len(sentences)} sentences "
                f"(kept={len(prepared)}, forbidden={discarded_forbidden}, "
                f"mismatch={discarded_mismatch})",
            )
        total_tokens += len(sentence.tokens)
        if contains_forbidden_symbol(sentence.tokens):
            discarded_forbidden += 1
            continue

        try:
            processed = preprocess(
                PreprocessingInput(text=" ".join(sentence.tokens) + " ")
            )
        except Exception:
            discarded_mismatch += 1
            continue
        exact = len(processed.tokens) == len(sentence.tokens) and all(
            actual.form.strip() == gold
            for actual, gold in zip(processed.tokens, sentence.tokens, strict=True)
        )
        if not exact:
            discarded_mismatch += 1
            continue

        labels = [LABEL_TO_CATEGORY[label] for label in sentence.raw_labels]
        prepared.append(
            PreparedSentence(
                features=sentence_features(processed.tokens, processed.morph_features),
                labels=labels,
            )
        )
        kept_tokens += len(labels)

    stats = PreparationStats(
        total_sentences=len(sentences),
        kept_sentences=len(prepared),
        discarded_forbidden_sentences=discarded_forbidden,
        discarded_mismatch_sentences=discarded_mismatch,
        total_tokens=total_tokens,
        kept_tokens=kept_tokens,
    )
    log(
        "finished sentence preparation "
        f"({stats.kept_sentences}/{stats.total_sentences} kept, "
        f"{stats.discarded_forbidden_sentences} forbidden, "
        f"{stats.discarded_mismatch_sentences} mismatch) in "
        f"{format_seconds(time.perf_counter() - started_at)}"
    )
    return prepared, stats


def load_split(
    dataset_names: Sequence[str], split_name: str
) -> tuple[list[PreparedSentence], dict[str, dict[str, int]]]:
    """Load and prepare a named split from one or more datasets."""
    return load_split_with_cache(dataset_names, split_name, cache_dir=None)


def load_split_with_cache(
    dataset_names: Sequence[str],
    split_name: str,
    *,
    cache_dir: Path | None,
) -> tuple[list[PreparedSentence], dict[str, dict[str, int]]]:
    """Load and prepare a named split from one or more datasets, with caching."""
    sentences: list[PreparedSentence] = []
    stats: dict[str, dict[str, int]] = {}
    for dataset_name in dataset_names:
        split_started_at = time.perf_counter()
        cache_path = _cache_path(cache_dir, dataset_name, split_name)
        if cache_path is not None and cache_path.is_file():
            try:
                prepared, prepared_stats = joblib.load(cache_path)
                log(
                    f"loaded cached {dataset_name}/{split_name} preparation "
                    f"in {format_seconds(time.perf_counter() - split_started_at)}"
                )
            except (EOFError, KeyError, ValueError):
                cache_path.unlink(missing_ok=True)
                log(f"rebuilding corrupted cache for {dataset_name}/{split_name}")
                prepared, prepared_stats = _prepare_dataset_split(
                    dataset_name,
                    split_name,
                )
                atomic_joblib_dump((prepared, prepared_stats), cache_path)
        else:
            log(f"preparing {dataset_name}/{split_name} from source")
            prepared, prepared_stats = _prepare_dataset_split(dataset_name, split_name)
            if cache_path is not None:
                atomic_joblib_dump((prepared, prepared_stats), cache_path)
                log(f"cached {dataset_name}/{split_name} preparation to {cache_path}")
        sentences.extend(prepared)
        stats[dataset_name] = prepared_stats.as_dict()
        log(
            f"finished {dataset_name}/{split_name} with "
            f"{prepared_stats.kept_sentences} kept sentences in "
            f"{format_seconds(time.perf_counter() - split_started_at)}"
        )
    return sentences, stats


def atomic_joblib_dump(value: Any, path: Path) -> None:
    """Write a joblib cache file atomically."""
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with contextlib.suppress(FileNotFoundError):
        temp_path.unlink()
    joblib.dump(value, temp_path)
    temp_path.replace(path)


def to_xy(
    sentences: Sequence[PreparedSentence],
) -> tuple[list[list[dict[str, object]]], list[list[str]]]:
    """Split prepared sentences into CRF matrices and label sequences."""
    return [sentence.features for sentence in sentences], [
        sentence.labels for sentence in sentences
    ]


def _cache_path(
    cache_dir: Path | None,
    dataset_name: str,
    split_name: str,
) -> Path | None:
    if cache_dir is None:
        return None
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{dataset_name}_{split_name}_{FEATURE_SET_VERSION}.joblib"


def _prepare_dataset_split(
    dataset_name: str,
    split_name: str,
) -> tuple[list[PreparedSentence], PreparationStats]:
    raw_sentences = read_labeled_sentences(
        dataset_dir(dataset_name) / f"{split_name}.txt"
    )
    return prepare_sentences(raw_sentences)
