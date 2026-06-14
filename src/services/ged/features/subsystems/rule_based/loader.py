"""YAML rule loader for the GED rule-based detector.

Reads *.yaml files from a rules directory
validates each entry against YamlRuleSchema
compiles it into a Python callable
registers it into a RuleRegistry instance.

Authors:
    Amir Anwar
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import yaml
from loguru import logger
from pydantic import BaseModel, ConfigDict, ValidationError
from src.core.schemas import MorphAnalysis, Token
from src.core.utils.arabic import strip_diacritics
from src.services.ged.features.subsystems.rule_based.models import RuleEntry
from src.services.ged.features.subsystems.rule_based.registry import RuleRegistry
from src.services.ged.schemas import ErrorCategory, ProvenanceTier

# ###########################################################################
# Schemas
# ###########################################################################


class YamlPatternSchema(BaseModel):
    """Validated pattern block for a single-token YAML rule.

    All fields are optional except match. Every supplied condition is
    ANDed together.
    """

    model_config = ConfigDict(extra="forbid")

    match: Literal["token"] = "token"
    pos: str | None = None
    pos_not: str | None = None
    lemma_in: list[str] | None = None
    form_regex: str | None = None
    form_ends_with: str | None = None
    gender: str | None = None
    number: str | None = None


class YamlRuleSchema(BaseModel):
    """Validated top-level entry for a single YAML rule."""

    model_config = ConfigDict(extra="forbid")

    id: str
    category: ErrorCategory
    subtype: str
    tier: ProvenanceTier
    explanation: str
    pattern: YamlPatternSchema


# ###########################################################################
# pattrn compiler
# ###########################################################################


def _compile_token_pattern(pattern: YamlPatternSchema):
    """Compile a validated YamlPatternSchema into a filter callable.

    Args:
        pattern: pattern schema

    Returns:
        A callable (token: Token, morph: MorphAnalysis | None) -> bool
        that returns True when all conditions match.
    """
    form_regex = re.compile(pattern.form_regex) if pattern.form_regex else None

    def _matches(token: Token, morph: MorphAnalysis | None) -> bool:
        if pattern.pos is not None and (morph is None or morph.pos != pattern.pos):
            return False

        if pattern.pos_not is not None and (
            morph is not None and morph.pos == pattern.pos_not
        ):
            return False

        if pattern.lemma_in is not None and (
            morph is None or morph.lemma not in pattern.lemma_in
        ):
            return False

        if form_regex is not None and not form_regex.search(token.form):
            return False

        if pattern.form_ends_with is not None:
            clean = strip_diacritics(token.form)
            if not clean or clean[-1] != pattern.form_ends_with:
                return False

        if pattern.gender is not None and (
            morph is None or morph.gender != pattern.gender
        ):
            return False

        if pattern.number is not None and (
            morph is None or morph.number != pattern.number
        ):
            return False

        return True

    return _matches


# ###########################################################################
# Rule compiler
# ###########################################################################


def compile_yaml_rule(raw: dict):
    """Validate and compile a raw YAML rule dict.

    Args:
        raw: A single rule entry as parsed from YAML (plain dict).

    Returns:
        A tuple (rule_fn, rule_id, category, subtype, tier, explanation)
        ready to build a RuleEntry.

    Raises:
        pydantic.ValidationError: If any required field is missing, has the
            wrong type, or has an unknown enum value.
    """
    rule = YamlRuleSchema.model_validate(raw)

    matcher = _compile_token_pattern(rule.pattern)

    def rule_fn(
        text: str,
        tokens: list[Token],
        morph_features: list[list[MorphAnalysis]],
    ) -> list[tuple[int, int, int]]:
        hits: list[tuple[int, int, int]] = []
        for i, token in enumerate(tokens):
            morph = morph_features[i][0] if morph_features[i] else None
            if matcher(token, morph):
                hits.append((token.span[0], token.span[1], token.index))
        return hits

    rule_fn.__name__ = rule.id

    return rule_fn, rule.id, rule.category, rule.subtype, rule.tier, rule.explanation


# ###########################################################################
# Public loader
# ###########################################################################


def load_yaml_rules(rules_dir: Path, registry: RuleRegistry) -> int:
    """Load all *.yaml files in *rules_dir* into *registry*.

    Args:
        rules_dir: Directory containing *.yaml rule files.
        registry: The RuleRegistry instance to populate.

    Returns:
        The number of rules successfully loaded.
    """
    if not rules_dir.exists():
        logger.warning("YAML rules directory {} does not exist , skipping.", rules_dir)
        return 0

    # NOTE: sorted alphabetically to make loading more deterministic
    yaml_files = sorted(rules_dir.glob("*.yaml"))
    if not yaml_files:
        logger.warning("No *.yaml files found in {}.", rules_dir)
        return 0

    loaded = 0
    for yaml_file in yaml_files:
        try:
            with yaml_file.open(encoding="utf-8") as fh:
                entries = yaml.safe_load(fh)
        except Exception:
            logger.exception("Failed to parse YAML file {}, skipping.", yaml_file)
            continue

        if not isinstance(entries, list):
            logger.warning(
                "YAML file {} does not contain a rule list , skipping.", yaml_file
            )
            continue

        for raw in entries:
            rule_id = (
                raw.get("id", "<unknown>") if isinstance(raw, dict) else "<unknown>"
            )
            try:
                fn, rule_id, category, subtype, tier, explanation = compile_yaml_rule(
                    raw
                )
                entry = RuleEntry(
                    rule_id=rule_id,
                    category=category,
                    subtype=subtype,
                    tier=tier,
                    explanation=explanation,
                    fn=fn,
                )
                registry.register_entry(entry)
                loaded += 1
            except ValidationError as exc:
                logger.warning(
                    "YAML rule {!r} in {} failed validation , skipping.\n{}",
                    rule_id,
                    yaml_file,
                    exc,
                )
            except Exception:
                logger.exception(
                    "Failed to compile YAML rule {!r} in {} , skipping.",
                    rule_id,
                    yaml_file,
                )

    logger.info("Loaded {} YAML rules from {}.", loaded, rules_dir)
    return loaded
