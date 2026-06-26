"""GECController: Orchestrates Ontology, Dictionary, and Tagger."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from src.services.gec.schemas import GECInput, ModuleResult, ModuleStatus


class GECController:
    """Orchestrates Ontology, Dictionary, and Tagger modules."""

    def __init__(self, ontology, dictionary, tagger=None):
        """Initialize GECController with tagger, ontology, and dictionary modules."""
        self.modules = {
            "ONTOLOGY": ontology,
            "DICTIONARY": dictionary,
            # "TAG": tagger,
        }

    def run(self, request: GECInput) -> list[ModuleResult]:
        """Run all modules in parallel and collect results."""
        results: list[ModuleResult] = []

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_name = {
                executor.submit(module.run, request): name
                for name, module in self.modules.items()
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

                results.append(result)
        return results
