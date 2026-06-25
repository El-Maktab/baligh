"""Ranks spelling alternatives based on edit distance and frequency."""

import math

from loguru import logger

from src.core.schemas import Token
from src.core.utils.arabic import extract_affixes
from src.services.gec.utils.distance_utils import levenshtein

from .arramooz_client import ArramoozClient

DISTANCE_WEIGHT = 0.5
FREQUENCY_WEIGHT = 0.3
LENGTH_WEIGHT = 0.2
MORPHOLOGICAL_WEIGHT = 0.0
MAX_ALTERNATIVES = 10


class AlternativeRanker:
    """Ranks candidate spelling alternatives."""

    def __init__(self, arramooz_client: ArramoozClient | None = None):
        """Initializes the AlternativeRanker.

        Args:
            arramooz_client: Optional client for word-frequency lookups.
                If None, a default ArramoozClient is created lazily.
        """
        self._arramooz_client = arramooz_client
        self._owns_client = arramooz_client is None

    def _ensure_client(self) -> ArramoozClient:
        if self._arramooz_client is None:
            logger.info("Lazily creating ArramoozClient for AlternativeRanker")
            self._arramooz_client = ArramoozClient()
        return self._arramooz_client

    def rank_alternatives(
        self, original_word: Token, candidates: list[Token]
    ) -> list[Token]:
        """Ranks candidates based on a scoring formula.

        Score = DISTANCE_WEIGHT * dist_score
              + FREQUENCY_WEIGHT * freq_score
              + LENGTH_WEIGHT * length_score
              + MORPHOLOGICAL_WEIGHT * morphological_bonus

        dist_score uses levenshtein which gives reduced cost
        for similar Arabic characters (e.g. ا <-> أ costs 0.3).
        length_score rewards candidates with lengths close to the original.
        """
        if not candidates:
            logger.warning(
                "rank_alternatives called with no candidates for '{}'",
                original_word.form,
            )
            return []

        logger.debug(
            "Ranking {} candidates for '{}'", len(candidates), original_word.form
        )

        client = self._ensure_client()
        word_frequency = {}

        max_freq = 0
        for cand in candidates:
            _, cand_stem, _ = extract_affixes(cand)
            freq = client.get_word_frequency(cand_stem)
            word_frequency[cand.form] = freq
            if freq > max_freq:
                max_freq = freq

        if max_freq == 0:
            logger.warning(
                "All candidates have zero frequency for '{}'", original_word.form
            )

        orig_len = len(original_word.form)
        max_len_delta = max(1, orig_len)

        scored_candidates = []
        for cand in candidates:
            dist = levenshtein(original_word.form, cand.form, True)

            max_dist = max(1.0, float(len(original_word.form)))

            dist_score = 1.0 - (dist / max_dist)

            freq_score = (
                0
                if max_freq == 0
                else math.log(word_frequency[cand.form] + 1) / math.log(max_freq + 1)
            )

            cand_len = len(cand.form)
            len_delta = abs(cand_len - orig_len)
            length_score = max(0.0, 1.0 - (len_delta / max_len_delta))

            morphological_bonus = self._calculate_morphological_bonus(cand, {})

            score = (
                DISTANCE_WEIGHT * dist_score
                + FREQUENCY_WEIGHT * freq_score
                + LENGTH_WEIGHT * length_score
                + MORPHOLOGICAL_WEIGHT * morphological_bonus
            )
            scored_candidates.append((cand, score))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        top = scored_candidates[:MAX_ALTERNATIVES]
        if top:
            best_cand, best_score = top[0]
            logger.debug(
                "Top candidate for '{}': '{}' (score={:.4f})",
                original_word.form,
                best_cand.form,
                best_score,
            )

        return [cand for cand, _ in top]

    def _calculate_morphological_bonus(self, candidate: Token, context: dict) -> float:
        """Calculate a bonus score based on morphological agreement with context.

        (Placeholder for future implementation).
        """
        return 0.0
