"""Tests for the YAML rule loader.

Covers:
- compile_yaml_rule produces correct RuleEntry metadata
- Each pattern field (pos, pos_not, lemma_in, form_regex, form_ends_with,
    gender, number)
  works in isolation and in combination
- load_yaml_rules populates a registry from a temporary directory
- Missing rules directory is handled gracefully (no exception)
- Unknown category / tier values raise ValueError from compile_yaml_rule
- Malformed YAML entries are skipped without crashing the loader

Authors:
    Amir Anwar
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.services.ged.features.subsystems.rule_based import (
    RuleBasedDetector,  # noqa: F401
)
from src.services.ged.features.subsystems.rule_based.loader import (
    compile_yaml_rule,
    load_yaml_rules,
)
from src.services.ged.features.subsystems.rule_based.registry import (
    RuleRegistry,
    rule_registry,
)
from src.services.ged.schemas import ErrorCategory, ProvenanceTier

from tests.services.ged.rule_based.conftest import make_morph, make_token

# ###########################################################################
# Helpers
# ###########################################################################

_T = make_token
_M = make_morph


def _run(raw_rule: dict, text: str, tokens, morphs):
    """Compile a raw rule dict and immediately run it against the given input."""
    fn, *_ = compile_yaml_rule(raw_rule)
    return fn(text, tokens, morphs)


# ###########################################################################
# compile_yaml_rule
# ###########################################################################


class TestCompileMetadata:
    """compile_yaml_rule must return correct metadata for the RuleEntry."""

    _BASE = {
        "id": "TEST_META",
        "category": "OT",
        "subtype": "hamza",
        "tier": "tier_1_rule_derived",
        "explanation": "تفسير",
        "pattern": {"match": "token"},
    }

    def test_category_parsed(self):
        """Category strings should resolve to the orthography enum."""
        _, _, category, *_ = compile_yaml_rule(self._BASE)
        assert category == ErrorCategory.ORTHOGRAPHY

    def test_tier_parsed(self):
        """Tier strings should resolve to the matching provenance tier."""
        _, _, _, _, tier, _ = compile_yaml_rule(self._BASE)
        assert tier == ProvenanceTier.TIER_1_RULE_DERIVED

    def test_unknown_category_raises(self):
        """Unknown categories should fail validation."""
        bad = {**self._BASE, "category": "ZZ"}
        with pytest.raises(ValidationError, match="category"):
            compile_yaml_rule(bad)

    def test_unknown_tier_raises(self):
        """Unknown tiers should fail validation."""
        bad = {**self._BASE, "tier": "tier_99_magic"}
        with pytest.raises(ValidationError, match="tier"):
            compile_yaml_rule(bad)

    def test_unsupported_match_scope_raises(self):
        """Unsupported match scopes should fail validation."""
        bad = {**self._BASE, "pattern": {"match": "bigram"}}
        with pytest.raises(ValidationError, match="match"):
            compile_yaml_rule(bad)

    def test_extra_field_raises(self):
        """Unknown fields in the rule entry are rejected outright."""
        bad = {**self._BASE, "confidence": 0.9}
        with pytest.raises(ValidationError, match="confidence"):
            compile_yaml_rule(bad)

    def test_missing_required_field_raises(self):
        """Missing required fields produce a clear Pydantic error."""
        bad = {k: v for k, v in self._BASE.items() if k != "explanation"}
        with pytest.raises(ValidationError, match="explanation"):
            compile_yaml_rule(bad)


# ###########################################################################
# compile_yaml_rule , pattern fields
# ###########################################################################


class TestPatternFields:
    """Each pattern condition works correctly in isolation."""

    _BASE_RULE = {
        "id": "X",
        "category": "OT",
        "subtype": "test",
        "tier": "tier_1_rule_derived",
        "explanation": "x",
    }

    def _rule(self, pattern: dict) -> dict:
        return {**self._BASE_RULE, "pattern": {"match": "token", **pattern}}

    @pytest.mark.parametrize(
        "form,morph_pos,morph_kwargs,pattern,expected",
        [
            ("إلى", "PREP", {"lemma": "إلى"}, {"pos": "PREP"}, [(0, 3, 0)]),
            ("كتب", "VERB", {}, {"pos": "PREP"}, []),
        ],
    )
    def test_pos_condition(self, form, morph_pos, morph_kwargs, pattern, expected):
        """A POS constraint should fire only when the tag matches."""
        tok = _T(form, (0, len(form)), 0)
        morph = _M(0, morph_pos, **morph_kwargs)
        assert _run(self._rule(pattern), form, [tok], [[morph]]) == expected

    @pytest.mark.parametrize(
        "form,morph_pos,pattern,expected",
        [
            ("،", "PUNC", {"pos_not": "PUNC"}, []),
            ("كتب", "VERB", {"pos_not": "PUNC"}, [(0, 3, 0)]),
        ],
    )
    def test_pos_not_condition(self, form, morph_pos, pattern, expected):
        """A negated POS constraint should exclude only the banned tag."""
        tok = _T(form, (0, len(form)), 0)
        morph = _M(0, morph_pos)
        assert _run(self._rule(pattern), form, [tok], [[morph]]) == expected

    @pytest.mark.parametrize(
        "form,lemma,pattern,expected",
        [
            ("علي", "على", {"lemma_in": ["على", "إلى"]}, [(0, 3, 0)]),
            ("من", "من", {"lemma_in": ["على", "إلى"]}, []),
        ],
    )
    def test_lemma_in_condition(self, form, lemma, pattern, expected):
        """Lemma membership should behave like a simple whitelist."""
        tok = _T(form, (0, len(form)), 0)
        morph = _M(0, "PREP", lemma=lemma)
        assert _run(self._rule(pattern), form, [tok], [[morph]]) == expected

    @pytest.mark.parametrize(
        "form,pattern,expected",
        [
            ("اذهب", {"form_regex": "^ا"}, [(0, 4, 0)]),
            ("يذهب", {"form_regex": "^ا"}, []),
        ],
    )
    def test_form_regex_condition(self, form, pattern, expected):
        """Regex constraints should match only the intended surface forms."""
        tok = _T(form, (0, len(form)), 0)
        morph = _M(0, "VERB")
        assert _run(self._rule(pattern), form, [tok], [[morph]]) == expected

    def test_form_condition(self):
        """Exact form matching should only fire on the configured surface."""
        tok = _T("انه", (0, 3), 0)
        morph = _M(0, "PART", lemma="إِنَّ")
        assert _run(self._rule({"form": "انه"}), tok.form, [tok], [[morph]]) == [
            (0, 3, 0)
        ]

    def test_form_in_condition(self):
        """Exact-form lists should behave like a whitelist."""
        tok = _T("عن", (0, 2), 0)
        morph = _M(0, "PREP")
        assert _run(
            self._rule({"form_in": ["عن", "من"]}), tok.form, [tok], [[morph]]
        ) == [(0, 2, 0)]

    @pytest.mark.parametrize(
        "form,pattern,expected",
        [
            ("علي", {"form_ends_with": "ي"}, [(0, 3, 0)]),
            ("على", {"form_ends_with": "ي"}, []),
        ],
    )
    def test_form_ends_with_condition(self, form, pattern, expected):
        """Suffix constraints should only match the configured ending."""
        tok = _T(form, (0, len(form)), 0)
        morph = _M(0, "PREP")
        assert _run(self._rule(pattern), form, [tok], [[morph]]) == expected

    @pytest.mark.parametrize(
        "form,morph_kwargs,pattern,expected",
        [
            ("المدرسه", {"gender": "feminine"}, {"gender": "feminine"}, [(0, 7, 0)]),
            ("المدرس", {"gender": "masculine"}, {"gender": "feminine"}, []),
        ],
    )
    def test_gender_condition(self, form, morph_kwargs, pattern, expected):
        """Gender constraints should match only the requested gender."""
        tok = _T(form, (0, len(form)), 0)
        morph = _M(0, "NOUN", **morph_kwargs)
        assert _run(self._rule(pattern), form, [tok], [[morph]]) == expected

    @pytest.mark.parametrize(
        "form,morph_kwargs,pattern,expected",
        [
            ("الطلاب", {"number": "plural"}, {"number": "plural"}, [(0, 6, 0)]),
            ("الطالب", {"number": "singular"}, {"number": "plural"}, []),
        ],
    )
    def test_number_condition(self, form, morph_kwargs, pattern, expected):
        """Number constraints should match only the requested number."""
        tok = _T(form, (0, len(form)), 0)
        morph = _M(0, "NOUN", **morph_kwargs)
        assert _run(self._rule(pattern), form, [tok], [[morph]]) == expected

    @pytest.mark.parametrize(
        "morph_kwargs,pattern,expected",
        [
            (
                {
                    "case": "nominative",
                    "definiteness": "definite",
                    "person": "third",
                    "tense": "present",
                    "mood": "indicative",
                },
                {
                    "case": "nominative",
                    "definiteness": "definite",
                    "person": "third",
                    "tense": "present",
                    "mood": "indicative",
                },
                [(0, 4, 0)],
            ),
            (
                {
                    "case": "accusative",
                    "definiteness": "definite",
                    "person": "third",
                    "tense": "present",
                    "mood": "indicative",
                },
                {
                    "case": "nominative",
                    "definiteness": "definite",
                    "person": "third",
                    "tense": "present",
                    "mood": "indicative",
                },
                [],
            ),
        ],
    )
    def test_extended_morph_fields(self, morph_kwargs, pattern, expected):
        """Case, definiteness, person, tense, and mood should all be matchable."""
        tok = _T("يفعل", (0, 4), 0)
        morph = _M(0, "VERB", **morph_kwargs)
        assert _run(self._rule(pattern), tok.form, [tok], [[morph]]) == expected

    @pytest.mark.parametrize(
        "form,lemma,pattern,expected",
        [
            (
                "علي",
                "على",
                {"pos": "PREP", "lemma_in": ["على", "إلى"], "form_ends_with": "ي"},
                [(0, 3, 0)],
            ),
            (
                "من",
                "من",
                {"pos": "PREP", "lemma_in": ["على", "إلى"], "form_ends_with": "ي"},
                [],
            ),
        ],
    )
    def test_and_combination_condition(self, form, lemma, pattern, expected):
        """Combined constraints should all pass before the rule fires."""
        tok = _T(form, (0, len(form)), 0)
        morph = _M(0, "PREP", lemma=lemma)
        assert _run(self._rule(pattern), form, [tok], [[morph]]) == expected


# ###########################################################################
# load_yaml_rules
# ###########################################################################


class TestLoadYamlRules:
    """load_yaml_rules populates a RuleRegistry from disk."""

    def test_loads_seed_yaml_file(self, tmp_path: Path):
        """A correctly formed YAML file registers its rules."""
        yaml_content = textwrap.dedent("""\
            - id: TMP_RULE_1
              category: OT
              subtype: hamza
              tier: tier_1_rule_derived
              explanation: "تفسير"
              pattern:
                match: token
                pos: PREP
                form_ends_with: "ي"
        """)
        (tmp_path / "test_rules.yaml").write_text(yaml_content, encoding="utf-8")

        reg = RuleRegistry()
        count = load_yaml_rules(tmp_path, reg)

        assert count == 1
        assert len(reg.list_rules()) == 1
        assert reg.list_rules()[0].rule_id == "TMP_RULE_1"

    def test_missing_directory_returns_zero(self, tmp_path: Path):
        """Non-existent directory logs a warning but does not raise."""
        reg = RuleRegistry()
        count = load_yaml_rules(tmp_path / "nonexistent", reg)
        assert count == 0

    def test_malformed_entry_skipped(self, tmp_path: Path):
        """An entry with an unknown category is skipped; valid entries still load."""
        yaml_content = textwrap.dedent("""\
            - id: BAD_RULE
              category: ZZ
              subtype: bad
              tier: tier_1_rule_derived
              explanation: "x"
              pattern:
                match: token

            - id: GOOD_RULE
              category: OT
              subtype: good
              tier: tier_1_rule_derived
              explanation: "y"
              pattern:
                match: token
        """)
        (tmp_path / "mixed.yaml").write_text(yaml_content, encoding="utf-8")

        reg = RuleRegistry()
        count = load_yaml_rules(tmp_path, reg)

        assert count == 1
        assert reg.list_rules()[0].rule_id == "GOOD_RULE"

    def test_seed_orthography_yaml_loads(self):
        """The real rules/orthography.yaml ships with valid entries."""
        from pathlib import Path as P

        rules_dir = (
            P(__file__).parent.parent.parent.parent.parent
            / "src"
            / "services"
            / "ged"
            / "features"
            / "subsystems"
            / "rule_based"
            / "rules"
        )
        reg = RuleRegistry()
        count = load_yaml_rules(rules_dir, reg)
        rule_ids = {entry.rule_id for entry in reg.list_rules()}

        assert count >= 50
        assert "OT_ALIF_MAQSURA_ALA" in rule_ids
        assert "SY_LAM_JUSSIVE" in rule_ids
        assert "OT_HAMZA_PREP" not in rule_ids
        assert "OT_HAMZA_ANNA" not in rule_ids
        assert "OT_ALIF_MAQSURA_PREP" not in rule_ids


class TestSequencePatterns:
    """Sequence mode should validate cleanly and match left-to-right windows."""

    _BASE_RULE = {
        "id": "SEQ_X",
        "category": "SY",
        "subtype": "sequence_test",
        "tier": "tier_1_rule_derived",
        "explanation": "x",
    }

    def _rule(self, pattern: dict) -> dict:
        return {**self._BASE_RULE, "pattern": {"match": "sequence", **pattern}}

    def test_valid_sequence_rule(self):
        """A well-formed sequence rule should compile and flag the selected token."""
        raw_rule = self._rule(
            {
                "tokens": [{"form": "لم"}, {"pos": "VERB", "mood": "indicative"}],
                "flag_token": 1,
            }
        )
        tokens = [_T("لم", (0, 2), 0), _T("يجري", (3, 7), 1)]
        morphs = [[_M(0, "PART")], [_M(1, "VERB", tense="present", mood="indicative")]]

        assert _run(raw_rule, "لم يجري", tokens, morphs) == [(3, 7, 1)]

    def test_invalid_flag_token_raises(self):
        """flag_token must point at one of the declared sequence token specs."""
        with pytest.raises(ValidationError, match="flag_token"):
            compile_yaml_rule(
                self._rule(
                    {
                        "tokens": [{"form": "لم"}, {"pos": "VERB"}],
                        "flag_token": 2,
                    }
                )
            )

    def test_invalid_tokens_length_raises(self):
        """Sequence rules require at least two token specs."""
        with pytest.raises(ValidationError, match="at least 2"):
            compile_yaml_rule(self._rule({"tokens": [{"form": "لم"}], "flag_token": 0}))

    def test_sequence_schema_rejects_top_level_token_fields(self):
        """Sequence rules should keep token matchers inside the tokens list."""
        with pytest.raises(ValidationError, match="top-level token fields"):
            compile_yaml_rule(
                {
                    **self._BASE_RULE,
                    "pattern": {
                        "match": "sequence",
                        "form": "لم",
                        "tokens": [{"form": "لم"}, {"pos": "VERB"}],
                        "flag_token": 1,
                    },
                }
            )

    def test_sequence_matching_without_punctuation_skipping(self):
        """Default sequence matching should fail across punctuation boundaries."""
        raw_rule = self._rule(
            {
                "tokens": [{"form": "عن"}, {"form": "ما"}, {"pos": "VERB"}],
                "flag_token": 0,
            }
        )
        tokens = [
            _T("عن", (0, 2), 0),
            _T("،", (2, 3), 1),
            _T("ما", (4, 6), 2),
            _T("أصابك", (7, 12), 3),
        ]
        morphs = [
            [_M(0, "PREP")],
            [_M(1, "PUNC")],
            [_M(2, "PART")],
            [_M(3, "VERB", tense="past")],
        ]

        assert _run(raw_rule, "عن ، ما أصابك", tokens, morphs) == []

    def test_sequence_matching_with_punctuation_skipping(self):
        """Sequence rules can optionally skip punctuation between matched tokens."""
        raw_rule = self._rule(
            {
                "tokens": [{"form": "عن"}, {"form": "ما"}, {"pos": "VERB"}],
                "flag_token": 0,
                "skip_punc": True,
            }
        )
        tokens = [
            _T("عن", (0, 2), 0),
            _T("،", (2, 3), 1),
            _T("ما", (4, 6), 2),
            _T("أصابك", (7, 12), 3),
        ]
        morphs = [
            [_M(0, "PREP")],
            [_M(1, "PUNC")],
            [_M(2, "PART")],
            [_M(3, "VERB", tense="past")],
        ]

        assert _run(raw_rule, "عن ، ما أصابك", tokens, morphs) == [(0, 2, 0)]


def test_rule_registry_has_no_duplicate_ids():
    """The live registry should not contain duplicate rule ids."""
    rule_ids = [entry.rule_id for entry in rule_registry.list_rules()]
    assert len(rule_ids) == len(set(rule_ids))


def test_retired_legacy_ids_are_absent_from_live_registry():
    """Only the broad hamza rule should remain live among the legacy ids."""
    rule_ids = {entry.rule_id for entry in rule_registry.list_rules()}
    assert "OT_HAMZA_PREP" in rule_ids
    assert "OT_HAMZA_ANNA" not in rule_ids
    assert "OT_ALIF_MAQSURA_PREP" not in rule_ids


def test_run_all_generic_hamza_rule_produces_a_single_hit():
    """The restored broad hamza rule should emit one span for a simple token."""
    tok = _T("الى", (0, 3), 0)
    morph = _M(0, "PREP", lemma="إِلَى")

    spans = rule_registry.run_all(tok.form, [tok], [[morph]])

    hits = [span for span in spans if span.span == (0, 3)]
    assert len(hits) == 1
