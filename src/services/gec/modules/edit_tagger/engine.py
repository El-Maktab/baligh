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

    def process(self, input_txt: GECInput) -> ModuleResult:
        try:
            conf, tokens, tags = self.predictor.predict(input_txt.text)
            new_text = self.rewriter.apply_tag(tokens, tags)
            candidate_edits = self.form_candidates(input_txt, new_text, conf)

            return ModuleResult(
                module_name=ModuleName.TAG,
                status=ModuleStatus.CORRECT,
                candidate_edits=candidate_edits,
            )
        except Exception:
            return ModuleResult(
                module_name=ModuleName.TAG,
                status=ModuleStatus.ERROR,
                candidate_edits=[],
            )

    def form_candidates(
        self,
        payload: GECInput,
        text: str,
        conf,
    ) -> list[CandidateEdit]:
        """Convert model output into CandidateEdit objects.

        Placeholder implementation returns an empty list.
        """
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
                    edit_confidence=conf,
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
