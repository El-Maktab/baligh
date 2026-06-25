"""Loader for curated lexicon GED patterns.

Authors:
    Amir Anwar
"""

from __future__ import annotations

from pathlib import Path

import yaml
from loguru import logger
from pydantic import ValidationError

from src.services.ged.detectors.lexicon.models import LexiconPattern


def load_patterns(path: Path) -> list[LexiconPattern]:
    """Load patterns from YAML file."""
    if not path.exists():
        logger.warning("Lexicon pattern file {} does not exist, skipping.", path)
        return []

    try:
        with path.open(encoding="utf-8") as fh:
            entries = yaml.safe_load(fh)
    except Exception:
        logger.exception("Failed to parse lexicon pattern file {}.", path)
        return []

    if not isinstance(entries, list):
        logger.warning("Lexicon pattern file {} does not contain a list.", path)
        return []

    patterns: list[LexiconPattern] = []
    for raw in entries:
        pattern_id = (
            raw.get("id", "<unknown>") if isinstance(raw, dict) else "<unknown>"
        )
        try:
            patterns.append(LexiconPattern.model_validate(raw))
        except ValidationError as exc:
            logger.warning(
                "Lexicon pattern {!r} in {} failed validation, skipping.\n{}",
                pattern_id,
                path,
                exc,
            )

    logger.info("Loaded {} lexicon patterns from {}.", len(patterns), path)
    return patterns
