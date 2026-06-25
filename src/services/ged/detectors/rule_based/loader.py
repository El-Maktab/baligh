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
from src.services.ged.detectors.rule_based.models import RuleEntry
from src.services.ged.detectors.rule_based.registry import RuleRegistry
from src.services.ged.schemas import ErrorCategory, ProvenanceTier

# ###########################################################################
# Schemas
# ###########################################################################


class YamlTokenSpecSchema(BaseModel):
    """Validated token matcher used by token and sequence YAML rules."""

    model_config = ConfigDict(extra="forbid")

    form: str | None = None
    form_in: list[str] | None = None
    pos: str | None = None
    pos_not: str | None = None
    lemma_in: list[str] | None = None
    form_regex: str | None = None
    form_ends_with: str | None = None
    gender: str | None = None
    number: str | None = None
    case: str | None = None
    definiteness: str | None = None
    person: str | None = None
    tense: str | None = None
    mood: str | None = None


class YamlPatternSchema(YamlTokenSpecSchema):
    """Validated pattern block for token and sequence YAML rules."""

    match: Literal["token", "sequence"] = "token"
    tokens: list[YamlTokenSpecSchema] | None = None
    flag_token: int | None = None
    skip_punc: bool = False

    def model_post_init(self, __context) -> None:
        """Validate fields that depend on the selected match mode."""
        token_fields = (
            "form",
            "form_in",
            "pos",
            "pos_not",
            "lemma_in",
            "form_regex",
            "form_ends_with",
            "gender",
            "number",
            "case",
            "definiteness",
            "person",
            "tense",
            "mood",
        )

        if self.match == "token":
            if self.tokens is not None:
                raise ValueError("tokens is only allowed when match=sequence")
            if self.flag_token is not None:
                raise ValueError("flag_token is only allowed when match=sequence")
            if self.skip_punc:
                raise ValueError("skip_punc is only allowed when match=sequence")
            return

        if self.tokens is None or len(self.tokens) < 2:
            raise ValueError("sequence rules require at least 2 token specs")

        if self.flag_token is None:
            raise ValueError("sequence rules require flag_token")

        if self.flag_token < 0 or self.flag_token >= len(self.tokens):
            raise ValueError("flag_token must point to a valid sequence token")

        for field_name in token_fields:
            if getattr(self, field_name) is not None:
                raise ValueError(
                    "top-level token fields are not allowed when match=sequence"
                )


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


def _compile_token_pattern(pattern: YamlTokenSpecSchema):
    """Compile a validated token spec into a filter callable.

    Args:
        pattern: token spec schema

    Returns:
        A callable (token: Token, morph: MorphAnalysis | None) -> bool
        that returns True when all conditions match.
    """
    form_regex = re.compile(pattern.form_regex) if pattern.form_regex else None

    def _matches(token: Token, morph: MorphAnalysis | None) -> bool:
        if pattern.form is not None and token.form != pattern.form:
            return False

        if pattern.form_in is not None and token.form not in pattern.form_in:
            return False

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

        if pattern.case is not None and (morph is None or morph.case != pattern.case):
            return False

        if pattern.definiteness is not None and (
            morph is None or morph.definiteness != pattern.definiteness
        ):
            return False

        if pattern.person is not None and (
            morph is None or morph.person != pattern.person
        ):
            return False

        if pattern.tense is not None and (
            morph is None or morph.tense != pattern.tense
        ):
            return False

        if pattern.mood is not None and (morph is None or morph.mood != pattern.mood):
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

    def _first_morph(index: int, morph_features: list[list[MorphAnalysis]]):
        return morph_features[index][0] if morph_features[index] else None

    if rule.pattern.match == "token":
        matcher = _compile_token_pattern(rule.pattern)

        def rule_fn(
            text: str,
            tokens: list[Token],
            morph_features: list[list[MorphAnalysis]],
        ) -> list[tuple[int, int, int]]:
            hits: list[tuple[int, int, int]] = []
            for i, token in enumerate(tokens):
                morph = _first_morph(i, morph_features)
                if matcher(token, morph):
                    hits.append((token.span[0], token.span[1], token.index))
            return hits

    else:
        assert rule.pattern.tokens is not None
        assert rule.pattern.flag_token is not None

        matchers = [
            _compile_token_pattern(token_spec) for token_spec in rule.pattern.tokens
        ]
        flag_token = rule.pattern.flag_token
        skip_punc = rule.pattern.skip_punc

        def rule_fn(
            text: str,
            tokens: list[Token],
            morph_features: list[list[MorphAnalysis]],
        ) -> list[tuple[int, int, int]]:
            hits: list[tuple[int, int, int]] = []
            n_tokens = len(tokens)

            for start in range(n_tokens):
                matched_indices: list[int] = []
                current = start

                for seq_index, matcher in enumerate(matchers):
                    if seq_index > 0 and skip_punc:
                        while current < n_tokens:
                            morph = _first_morph(current, morph_features)
                            if morph is None or morph.pos != "PUNC":
                                break
                            current += 1

                    if current >= n_tokens:
                        break

                    token = tokens[current]
                    morph = _first_morph(current, morph_features)
                    if not matcher(token, morph):
                        break

                    matched_indices.append(current)
                    current += 1

                if len(matched_indices) != len(matchers):
                    continue

                flagged_index = matched_indices[flag_token]
                flagged_token = tokens[flagged_index]
                hits.append(
                    (
                        flagged_token.span[0],
                        flagged_token.span[1],
                        flagged_token.index,
                    )
                )

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
