"""Orchestrates the dictionary module's sub-components."""

from collections import OrderedDict

from loguru import logger

from src.core.schemas import Token
from src.services.gec.schemas import (
    CandidateEdit,
    GECInput,
    ModuleName,
    ModuleResult,
    ModuleStatus,
)
from src.services.ged.schemas import ErrorCategory, ErrorSource

from .alternative_ranker import MAX_ALTERNATIVES, AlternativeRanker
from .arramooz_client import ArramoozClient
from .spell_checker import SpellChecker

_GED_FLAGGED_CONFIDENCE = 0.9
_CANDIDATE_CACHE_SIZE = 2048


class DictionaryEngine:
    """Integrates spell checking and ranking to process GEC inputs.

    Generates spelling suggestions only for tokens that the GED lexicon detector
    already flagged as orthography mistakes.
    """

    def __init__(self, arramooz_client: ArramoozClient | None = None) -> None:
        """Initializes the DictionaryEngine."""
        self.arramooz_client = (
            arramooz_client if arramooz_client is not None else ArramoozClient()
        )
        self.spell_checker = SpellChecker(self.arramooz_client)
        self.alternative_ranker = AlternativeRanker(self.arramooz_client)
        self._candidate_cache: OrderedDict[tuple[str, str], list[str]] = OrderedDict()
        logger.info("DictionaryEngine initialized successfully")

    def close(self) -> None:
        """Release database connections."""
        self.arramooz_client.close()
        logger.info("DictionaryEngine closed")

    def process(self, input_data: GECInput) -> ModuleResult:
        """Process the input and return spelling corrections.

        Strategy:
            1.  Collect token indices flagged by the GED lexicon detector as
                ORTHOGRAPHY errors.
            2.  Generate candidates only for those flagged tokens.

        Args:
            input_data: The GEC pipeline input containing text, tokens,
                morph features, and error spans from GED.

        Returns:
            ModuleResult with spelling correction edits.
        """
        ged_flagged: set[int] = set()
        edits: list[CandidateEdit] = []

        logger.info(
            "DictionaryEngine.process | tokens={} errors_span={}",
            len(input_data.tokens),
            len(input_data.errors_span),
        )

        # Tokens flagged by the GED lexicon detector as orthography errors
        for error_span in input_data.errors_span:
            if (
                error_span.category != ErrorCategory.ORTHOGRAPHY
                or ErrorSource.LEXICON_MATCHER not in error_span.sources
            ):
                continue
            for tidx in error_span.token_refs:
                if tidx in ged_flagged:
                    continue
                ged_flagged.add(tidx)
                edit = self._check_token(input_data, tidx, _GED_FLAGGED_CONFIDENCE)
                if edit is not None:
                    edits.append(edit)

        logger.debug("GED-flagged orthography tokens: {}", len(ged_flagged))

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
    ) -> CandidateEdit | None:
        """Run spell-check + ranking on a single token.

        Args:
            input_data: The full GEC input (for token/schedule access).
            token_index: Index of the token to check.
            base_confidence: Confidence floor for the resulting edit.

        Returns:
            A CandidateEdit or None if no candidates.
        """
        if token_index < 0 or token_index >= len(input_data.tokens):
            logger.warning(
                "Token index {} out of range [0, {})",
                token_index,
                len(input_data.tokens),
            )
            return None

        token = input_data.tokens[token_index]
        ranked_forms = self._get_ranked_forms(token)
        if not ranked_forms:
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
                    and ErrorSource.LEXICON_MATCHER in error_span.sources
                    and token_index in error_span.token_refs
                ):
                    confidence = max(confidence, error_span.confidence)
                    break

        return CandidateEdit(
            span=(start, end),
            token_refs=[token_index],
            alternatives=ranked_forms,
            correction=ranked_forms[0],
            edit_confidence=min(confidence, 1.0),
        )

    def _get_ranked_forms(self, token: Token) -> list[str]:
        """Return cached ranked forms for a token surface when available."""
        if not token.form or not token.affix_structure:
            logger.warning("Token missing form or affix_structure: {}", token)
            return []
        cache_key = (token.form, token.affix_structure)
        cached = self._candidate_cache.get(cache_key)
        if cached is not None:
            self._candidate_cache.move_to_end(cache_key)
            return list(cached)

        candidates = self.spell_checker.generate_candidates(token)
        if not candidates:
            self._remember_ranked_forms(cache_key, [])
            return []

        ranked_candidates = self.alternative_ranker.rank_alternatives(
            token,
            candidates,
        )
        ranked_forms = [c.form for c in ranked_candidates[:MAX_ALTERNATIVES]]
        self._remember_ranked_forms(cache_key, ranked_forms)
        return list(ranked_forms)

    def _remember_ranked_forms(
        self,
        cache_key: tuple[str, str],
        ranked_forms: list[str],
    ) -> None:
        """Store ranked forms in a small LRU cache."""
        self._candidate_cache[cache_key] = list(ranked_forms)
        self._candidate_cache.move_to_end(cache_key)
        if len(self._candidate_cache) > _CANDIDATE_CACHE_SIZE:
            self._candidate_cache.popitem(last=False)
