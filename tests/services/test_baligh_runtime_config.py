"""Tests for Baligh runtime-config-driven wiring."""

from __future__ import annotations

from src.runtime_config import load_runtime_config
from src.services.baligh import Baligh
from src.services.gec.schemas import ModuleName


class _DummyNWS:
    def predict(self, input):  # noqa: ANN001, D401
        """Return a placeholder value."""
        return input


class _DummyRanker:
    def rank(self, input):  # noqa: ANN001, D401
        """Return a placeholder value."""
        return input


def test_baligh_only_constructs_enabled_modules_and_detectors(monkeypatch) -> None:
    """Disabled GEC/GED components should not be constructed."""
    runtime_config = load_runtime_config().model_copy(deep=True)
    runtime_config.gec.modules.ontology.enabled = False
    runtime_config.gec.modules.dictionary.enabled = True
    runtime_config.gec.modules.tagger.enabled = False
    runtime_config.ged.detectors.lexicon.enabled = False
    runtime_config.ged.detectors.ml.enabled = False
    runtime_config.nws.enabled = False

    constructed: list[str] = []

    def _factory(name: str):
        class _Stub:
            def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
                constructed.append(name)

        return _Stub

    monkeypatch.setattr("src.services.baligh.OntologyService", _factory("ontology"))
    monkeypatch.setattr("src.services.baligh.DictionaryService", _factory("dictionary"))
    monkeypatch.setattr("src.services.baligh.EditTaggerService", _factory("tagger"))
    monkeypatch.setattr("src.services.baligh.RuleBasedDetector", _factory("rule_based"))
    monkeypatch.setattr("src.services.baligh.LexiconDetector", _factory("lexicon"))
    monkeypatch.setattr("src.services.baligh.MLDetector", _factory("ml"))
    monkeypatch.setattr("src.services.baligh.RankerService", lambda: _DummyRanker())

    baligh = Baligh(runtime_config=runtime_config)

    assert constructed == ["dictionary", "rule_based"]
    assert [name for name, _ in baligh.gec.modules] == [ModuleName.DICTIONARY]
    assert len(baligh.ged.subsystems) == 1
    assert baligh.nws is None


def test_run_nws_returns_empty_output_when_disabled(monkeypatch) -> None:
    """Disabled NWS should yield an empty output instead of loading models."""
    runtime_config = load_runtime_config().model_copy(deep=True)
    runtime_config.ged.detectors.rule_based.enabled = False
    runtime_config.ged.detectors.lexicon.enabled = False
    runtime_config.ged.detectors.ml.enabled = False
    runtime_config.gec.modules.ontology.enabled = False
    runtime_config.gec.modules.dictionary.enabled = False
    runtime_config.gec.modules.tagger.enabled = False
    runtime_config.nws.enabled = False

    preprocessing_output = type(
        "_PreprocessingOutput",
        (),
        {
            "tokens": [],
            "morph_features": [],
            "current_fragment": None,
            "mode": "WAC",
        },
    )()

    monkeypatch.setattr(
        "src.services.baligh.preprocess", lambda _input: preprocessing_output
    )
    monkeypatch.setattr("src.services.baligh.RankerService", lambda: _DummyRanker())

    baligh = Baligh(runtime_config=runtime_config)
    output = baligh.run_nws("ال")

    assert output.mode == "WAC"
    assert output.suggestions == []
