"""Orchestrates the dictionary module's sub-components."""

from loguru import logger

from src.services.gec.schemas import (
    DictionaryCandidateEdit,
    GECInput,
    ModuleName,
    ModuleResult,
    ModuleStatus,
)
from src.services.ged.schemas import ErrorCategory

from .alternative_ranker import MAX_ALTERNATIVES, AlternativeRanker
from .arramooz_client import ArramoozClient
from .spell_checker import SpellChecker

_GED_FLAGGED_CONFIDENCE = 0.9
_UNFLAGGED_OOV_CONFIDENCE = 0.5


class DictionaryEngine:
    """Integrates spell checking and ranking to process GEC inputs.

    Checks all tokens for OOV spelling errors, not just those flagged by GED.
    Tokens that appear in errors_span with ORTHOGRAPHY category
    receive a higher edit confidence than tokens discovered as OOV independently.
    """

    def __init__(self) -> None:
        """Initializes the DictionaryEngine."""
        self.arramooz_client = ArramoozClient()
        self.spell_checker = SpellChecker(self.arramooz_client)
        self.alternative_ranker = AlternativeRanker(self.arramooz_client)
        logger.info("DictionaryEngine initialized successfully")

    def process(self, input_data: GECInput) -> ModuleResult:
        """Process the input and return spelling corrections.

        Strategy:
            1.  Collect token indices flagged by GED as ORTHOGRAPHY
                errors. These are processed first with high confidence.
            2.  Scan every remaining token for OOV and generate candidates
                with lower confidence.

        Args:
            input_data: The GEC pipeline input containing text, tokens,
                morph features, and error spans from GED.

        Returns:
            ModuleResult with spelling correction edits.
        """
        ged_flagged: set[int] = set()
        edits: list[DictionaryCandidateEdit] = []

        logger.info(
            "DictionaryEngine.process | tokens={} errors_span={}",
            len(input_data.tokens),
            len(input_data.errors_span),
        )

        # Tokens flagged by GED as orthography errors
        for error_span in input_data.errors_span:
            if error_span.category != ErrorCategory.ORTHOGRAPHY:
                continue
            for tidx in error_span.token_refs:
                if tidx in ged_flagged:
                    continue
                ged_flagged.add(tidx)
                edit = self._check_token(input_data, tidx, _GED_FLAGGED_CONFIDENCE)
                if edit is not None:
                    edits.append(edit)

        logger.debug("GED-flagged orthography tokens: {}", len(ged_flagged))

        # Scan remaining tokens for OOV errors GED may have missed
        oov_count = 0
        for token in input_data.tokens:
            tidx = token.index
            if tidx in ged_flagged:
                continue
            if not self.spell_checker.is_oov(token):
                continue
            oov_count += 1
            edit = self._check_token(input_data, tidx, _UNFLAGGED_OOV_CONFIDENCE)
            if edit is not None:
                edits.append(edit)

        logger.debug("Unflagged OOV tokens discovered: {}", oov_count)

        status = ModuleStatus.INCORRECT if edits else ModuleStatus.CORRECT
        logger.info(
            "DictionaryEngine.process complete | edits={} status={}",
            len(edits),
            status.value,
        )
        return ModuleResult(
            module_name=ModuleName.DICTIONARY,
            status=status,
            candidate_edits=edits,
        )

    def _check_token(
        self,
        input_data: GECInput,
        token_index: int,
        base_confidence: float,
    ) -> DictionaryCandidateEdit | None:
        """Run spell-check + ranking on a single token.

        Args:
            input_data: The full GEC input (for token/schedule access).
            token_index: Index of the token to check.
            base_confidence: Confidence floor for the resulting edit.

        Returns:
            A DictionaryCandidateEdit or None if no candidates.
        """
        if token_index < 0 or token_index >= len(input_data.tokens):
            logger.warning(
                "Token index {} out of range [0, {})",
                token_index,
                len(input_data.tokens),
            )
            return None

        token = input_data.tokens[token_index]
        candidates = self.spell_checker.generate_candidates(token)
        if not candidates:
            logger.warning(
                "No spelling candidates for token '{}' at index {}",
                token.form,
                token_index,
            )
            return None

        ranked_candidates = self.alternative_ranker.rank_alternatives(
            token,
            candidates,
        )
        if not ranked_candidates:
            logger.warning(
                "No ranked alternatives for token '{}' at index {}",
                token.form,
                token_index,
            )
            return None

        start, end = token.span

        # Boost confidence slightly when GED already flagged the token
        confidence = base_confidence
        if base_confidence >= _GED_FLAGGED_CONFIDENCE:
            for error_span in input_data.errors_span:
                if (
                    error_span.category == ErrorCategory.ORTHOGRAPHY
                    and token_index in error_span.token_refs
                ):
                    confidence = max(confidence, error_span.confidence)
                    break

        ranked_forms = [c.form for c in ranked_candidates[:MAX_ALTERNATIVES]]

        return DictionaryCandidateEdit(
            span=(start, end),
            token_refs=[token_index],
            alternatives=ranked_forms,
            correction=ranked_forms[0],
            edit_confidence=min(confidence, 1.0),
        )
