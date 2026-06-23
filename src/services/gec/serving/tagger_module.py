from src.services.gec.schemas import EditTaggerCandidateEdit, GECInput, ModuleName, ModuleResult, ModuleStatus
from src.services.gec.serving.module import GECModule


class EditTaggerService(GECModule):
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer

    def run(self, input: GECInput) -> ModuleResult:
        try:
            candidate_edits: list[EditTaggerCandidateEdit] = []
            
            #TODO: Do what you gotta do (get candidate edits)

            return ModuleResult(
                module_name=ModuleName.TAG,
                status=ModuleStatus.CORRECT,
                candidate_edits=candidate_edits,
            )
        except Exception: 
            return ModuleResult( module_name=ModuleName.TAG, status=ModuleStatus.ERROR, candidate_edits=[], )
        