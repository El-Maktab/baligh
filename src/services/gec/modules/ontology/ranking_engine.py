"""Ranking Engine for grammatical correction candidates."""

from src.core.utils.arabic import strip_diacritics
from src.services.gec.schemas import OntologyCandidateEdit


def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes the Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (0 if c1 == c2 else 1)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


class RankingEngine:
    """Ranks grammatical candidates using composite confidence scoring."""

    def rank_candidates(
        self,
        candidates: list[OntologyCandidateEdit],
        original_token: str,
    ) -> list[OntologyCandidateEdit]:
        """Ranks candidates using composite scoring and updates their confidence/ranks.

        Args:
            candidates: List of proposed OntologyCandidateEdit objects.
            original_token: The original word before correction.

        Returns:
            Sorted list of candidates with updated ranks and confidence.
        """
        scored_candidates = []

        for candidate in candidates:
            # 1. Levenshtein Distance score
            dist_raw = levenshtein_distance(original_token, candidate.correction)
            dist_strip = levenshtein_distance(
                strip_diacritics(original_token), strip_diacritics(candidate.correction)
            )

            dist = (dist_raw + dist_strip) / 2.0
            lev_score = 1.0 / (1.0 + dist)

            # 2. Modification Count score (number of character edits)
            mod_score = 1.0 / (
                1.0 + abs(len(original_token) - len(candidate.correction))
            )

            # 4. Constraint quality (default to 1.0)
            constraint_score = 1.0

            # Weighted composite (weights configurable, Levenshtein dominates)
            weights = {
                "levenshtein": 0.6,
                "modifications": 0.1,
                "rule_confidence": 0.15,
                "constraint_quality": 0.15,
            }

            composite_confidence = (
                weights["levenshtein"] * lev_score
                + weights["modifications"] * mod_score
                + weights["constraint_quality"] * constraint_score
            )

            scored_candidates.append((candidate, composite_confidence))

        # Sort candidates descending by composite_score
        ranked_pairs = sorted(scored_candidates, key=lambda pair: pair[1], reverse=True)
        ranked = [pair[0] for pair in ranked_pairs]

        return ranked

    def rank_complete_sentences(
        self,
        candidates: list[OntologyCandidateEdit],
        original_sentence: str,
    ) -> list[OntologyCandidateEdit]:
        """Ranks complete sentence candidates by Levenshtein distance.

        Args:
            candidates: List of complete sentence OntologyCandidateEdit objects.
            original_sentence: The original input sentence.

        Returns:
            Sorted list of candidates, closest to original first.
        """
        scored_candidates = []

        for candidate in candidates:
            # Calculate Levenshtein distance from original sentence
            dist_raw = levenshtein_distance(original_sentence, candidate.correction)
            dist_strip = levenshtein_distance(
                strip_diacritics(original_sentence),
                strip_diacritics(candidate.correction),
            )

            # Average the two distances
            dist = (dist_raw + dist_strip) / 2.0

            # Convert to score (closer = higher score)
            lev_score = 1.0 / (1.0 + dist)

            # Blend with edit_confidence from the candidate
            composite_score = (lev_score * 0.7) + (candidate.edit_confidence * 0.3)

            scored_candidates.append((candidate, composite_score))

        # Sort by composite score descending
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # Assign ranks and update confidence
        ranked = []
        for rank, (candidate, score) in enumerate(scored_candidates, start=1):
            # Blend the score with original confidence
            candidate.edit_confidence = (score * 0.7) + (
                candidate.edit_confidence * 0.3
            )
            ranked.append(candidate)

        return ranked
