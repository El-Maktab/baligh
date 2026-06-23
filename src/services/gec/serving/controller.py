"""GECController: Orchestrates Ontology, Dictionary, and Tagger."""
from src.services.gec.serving.module import GECModule
from src.services.gec.schemas import GECInput, GECOutput, ModuleResult


class GECController:
    def __init__(
        self,
        tagger: GECModule,
        ontology: GECModule,
        dictionary: GECModule,
    ):
        self.modules = [
            tagger,
            ontology,
            dictionary,
        ]
    
    def correct(self, request: GECInput) -> GECOutput:
        results : list[ModuleResult] = [m.run(request) for m in self.modules]
        return GECOutput(results)