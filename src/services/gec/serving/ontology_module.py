
from src.services.gec.schemas import GECInput, ModuleName, ModuleResult, ModuleStatus, OntologyCandidateEdit
from src.services.gec.serving.module import GECModule


class OntologyService(GECModule):

    def __init__(self, ontology_engine):
        self.ontology_engine = ontology_engine

    def run(self, input: GECInput) -> ModuleResult:
        try:
            candidate_edits: list[OntologyCandidateEdit] = []
            #TODO: Do what you gotta do (get candidate edits)
            status = (
                ModuleStatus.CORRECT
                if candidate_edits
                else ModuleStatus.INCORRECT
            )

            return ModuleResult(
                module_name=ModuleName.ONTOLOGY,
                status=status,
                candidate_edits=candidate_edits,
            )

        except Exception:
            return ModuleResult(
                module_name=ModuleName.ONTOLOGY,
                status=ModuleStatus.ERROR,
                candidate_edits=[],
            )
