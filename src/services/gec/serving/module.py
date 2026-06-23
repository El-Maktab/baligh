from typing import Protocol

from src.services.gec.schemas import DictionaryCandidateEdit, EditTaggerCandidateEdit, GECInput, ModuleName, ModuleResult, ModuleStatus, OntologyCandidateEdit


class GECModule(Protocol):
    def run(self, input: GECInput) -> ModuleResult:
        ...
