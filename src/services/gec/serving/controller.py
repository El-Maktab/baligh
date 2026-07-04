"""GECController orchestration for enabled correction modules."""

from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.services.gec.schemas import GECInput, ModuleName, ModuleResult, ModuleStatus


class GECController:
    """Orchestrate the configured GEC modules."""

    def __init__(self, modules: Iterable[tuple[ModuleName, object]]):
        """Initialize GECController with the enabled modules in output order."""
        self.modules = list(modules)

    def run(self, request: GECInput) -> list[ModuleResult]:
        """Run enabled modules in parallel and collect results in config order."""
        if not self.modules:
            return []

        results_by_name: dict[ModuleName, ModuleResult] = {}
        with ThreadPoolExecutor(max_workers=len(self.modules)) as executor:
            future_to_name = {
                executor.submit(module.run, request): name
                for name, module in self.modules
            }

            for future in as_completed(future_to_name):
                module_name = future_to_name[future]

                try:
                    result = future.result()
                except Exception:
                    result = ModuleResult(
                        module_name=module_name,
                        status=ModuleStatus.ERROR,
                        candidate_edits=[],
                    )

                results_by_name[module_name] = result

        return [
            results_by_name[name] for name, _ in self.modules if name in results_by_name
        ]
