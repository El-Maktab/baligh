import json
from difflib import SequenceMatcher

from src.services.gec.config import LABEL2ID_PATH
from src.services.gec.modules.edit_tagger.inference.inference import (
    GECInferencePipeline,
)
from src.services.gec.modules.edit_tagger.preprocessing.aligner import Aligner
from src.services.gec.modules.edit_tagger.preprocessing.rewriter import Rewriter
from src.services.gec.schemas import (
    CandidateEdit,
    GECInput,
    ModuleName,
    ModuleResult,
    ModuleStatus,
)
from src.services.preprocessing.schemas import Token


class TaggerEngine:
    def __init__(self, model, tokenizer):
        self.rewriter = Rewriter()
        self.aligner = Aligner()

        with open(LABEL2ID_PATH, encoding="utf-8") as f:
            label2id = json.load(f)
        id2label = {v: k for k, v in label2id.items()}

        self.predictor = GECInferencePipeline(model, tokenizer, id2label)

    def process(self, payload: GECInput) -> ModuleResult:
        # try:
        tokens, tags = self.predictor.predict(payload.text)
        new_text = self.rewriter.apply_tag(tokens, tags)
        candidate_edits = self.form_candidates(payload, new_text)
        print(tokens)
        print(tags)

        print(new_text)
        print(candidate_edits)

        if len(candidate_edits) != 0:
            status = ModuleStatus.INCORRECT
        else:
            status = ModuleStatus.CORRECT

        return ModuleResult(
            module_name=ModuleName.TAG,
            status=status,
            candidate_edits=candidate_edits,
        )

    # except Exception:
    #     return ModuleResult(
    #         module_name=ModuleName.TAG,
    #         status=ModuleStatus.ERROR,
    #         candidate_edits=[],
    #     )

    def form_candidates(
        self,
        payload: GECInput,
        text: str,
    ) -> list[CandidateEdit]:
        """Convert model output into CandidateEdit objects."""
        original = payload.text
        matcher = SequenceMatcher(None, original, text)

        candidates: list[CandidateEdit] = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue

            token_refs = self.get_token_refs(payload.tokens, i1, i2)
            candidates.append(
                CandidateEdit(
                    span=(i1, i2),
                    token_refs=token_refs,
                    correction=text[j1:j2],
                    edit_confidence=0,
                )
            )
        return candidates

    def get_token_refs(self, tokens: list[Token], start: int, end: int) -> list[int]:
        refs = []

        for token in tokens:
            token_start, token_end = token.span

            if token_start < end and token_end > start:
                refs.append(token.index)
        return refs
