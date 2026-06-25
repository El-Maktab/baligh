"""Command-line interface for GED ML training.

Authors:
    Amir Anwar
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.services.ged.detectors.ml.artifact import DEFAULT_THRESHOLD
from src.services.ged.detectors.ml.training.export import train_and_export

DEFAULT_MODEL_NAME = "baligh-ged-crf-surface-morph-v2"
DEFAULT_ARTIFACT_VERSION = "0.2.0"
DEFAULT_THRESHOLDS = tuple(round(step / 100, 2) for step in range(5, 95, 5))


def main() -> None:
    """Train and export the morphology-aware GED CRF."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--train-datasets",
        nargs="+",
        default=["qalb14", "qalb15"],
    )
    parser.add_argument(
        "--dev-datasets",
        nargs="+",
        default=["qalb14", "qalb15"],
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=Path("artifacts/ged/ml/crf-surface-morph-v2/v0.2.0"),
    )
    parser.add_argument(
        "--artifact-version",
        default=DEFAULT_ARTIFACT_VERSION,
    )
    parser.add_argument(
        "--model-name",
        default=DEFAULT_MODEL_NAME,
    )
    parser.add_argument(
        "--c1-grid",
        default="0.05,0.1,0.2",
    )
    parser.add_argument(
        "--c2-grid",
        default="0.05,0.1,0.2",
    )
    parser.add_argument(
        "--max-iterations-grid",
        default="100,150",
    )
    parser.add_argument(
        "--thresholds",
        default=",".join(str(value) for value in DEFAULT_THRESHOLDS),
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("artifacts/ged/ml/.cache"),
    )
    args = parser.parse_args()

    manifest = train_and_export(
        train_datasets=args.train_datasets,
        dev_datasets=args.dev_datasets,
        artifact_dir=args.artifact_dir,
        artifact_version=args.artifact_version,
        model_name=args.model_name,
        c1_values=_parse_csv_floats(args.c1_grid),
        c2_values=_parse_csv_floats(args.c2_grid),
        max_iterations_values=_parse_csv_ints(args.max_iterations_grid),
        thresholds=_parse_csv_floats(args.thresholds) or [DEFAULT_THRESHOLD],
        cache_dir=args.cache_dir,
    )
    print(json.dumps(manifest["development_metrics"], ensure_ascii=False, indent=2))


def _parse_csv_floats(raw: str) -> list[float]:
    return [float(item) for item in raw.split(",") if item]


def _parse_csv_ints(raw: str) -> list[int]:
    return [int(item) for item in raw.split(",") if item]
