from src.services.gec.schemas import DictionaryCandidateEdit, GECInput, ModuleName, ModuleResult, ModuleStatus
from src.services.gec.serving.module import GECModule


class DictionaryService(GECModule):

    def __init__(self, dictionary_engine):
        self.dictionary_engine = dictionary_engine

    def run(self, input: GECInput) -> ModuleResult:
        try:
            candidate_edits: list[DictionaryCandidateEdit] = []
            #TODO: Do what you gotta do (get candidate edits)
            status = (
                ModuleStatus.CORRECT
                if candidate_edits
                else ModuleStatus.INCORRECT
            )

            return ModuleResult(
                module_name=ModuleName.DICTIONARY,
                status=status,
                candidate_edits=candidate_edits,
            )

        except Exception:
            return ModuleResult(
                module_name=ModuleName.DICTIONARY,
                status=ModuleStatus.ERROR,
                candidate_edits=[],
            )