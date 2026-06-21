"""CLI for eval."""

import argparse
import sys
from pathlib import Path

from loguru import logger

from src.services.ged.evaluation.datasets import DATASETS
from src.services.ged.evaluation.models import EvaluationConfig
from src.services.ged.evaluation.runner import EvaluationError, evaluate


def main() -> None:
    """Run GED."""
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="{time:HH:mm:ss} | {level:<7} | {message}",
    )

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        action="append",
        choices=tuple(DATASETS),
        dest="datasets",
        help="Dataset to evaluate; repeat to select multiple (default: all).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/ged/evaluation/report.json"),
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Evaluate at most N sentences per dataset.",
    )

    args = parser.parse_args()

    config = EvaluationConfig(
        datasets=tuple(args.datasets) if args.datasets else EvaluationConfig().datasets,
        output_path=args.output,
        limit=args.limit,
    )

    try:
        evaluate(config)
    except (EvaluationError, ValueError) as error:
        parser.exit(1, f"GED evaluation failed: {error}\n")


if __name__ == "__main__":
    main()
