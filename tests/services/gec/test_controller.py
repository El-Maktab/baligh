"""Tests for config-driven GEC module orchestration."""

from __future__ import annotations

from src.services.gec.schemas import GECInput, ModuleName, ModuleResult, ModuleStatus
from src.services.gec.serving.controller import GECController


class _StubModule:
    def __init__(self, result: ModuleResult) -> None:
        self.result = result

    def run(self, input: GECInput) -> ModuleResult:  # noqa: ARG002
        return self.result


def test_controller_returns_only_enabled_modules_in_config_order() -> None:
    """The controller should return only configured modules in a stable order."""
    controller = GECController(
        [
            (
                ModuleName.DICTIONARY,
                _StubModule(
                    ModuleResult(
                        module_name=ModuleName.DICTIONARY,
                        status=ModuleStatus.CORRECT,
                        candidate_edits=[],
                    )
                ),
            ),
            (
                ModuleName.TAG,
                _StubModule(
                    ModuleResult(
                        module_name=ModuleName.TAG,
                        status=ModuleStatus.CORRECT,
                        candidate_edits=[],
                    )
                ),
            ),
        ]
    )

    output = controller.run(
        GECInput(text="", tokens=[], morph_features=[], errors_span=[])
    )

    assert [result.module_name for result in output] == [
        ModuleName.DICTIONARY,
        ModuleName.TAG,
    ]
