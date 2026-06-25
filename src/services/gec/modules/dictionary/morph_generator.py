"""Generates valid morphological inflections for Arabic words using Arramooz."""

from typing import Any

from loguru import logger

from src.core.utils.arabic import (
    DAMMA,
    DAMMATAN,
    FATHA,
    FATHATAN,
    KASRA,
    KASRATAN,
    PAST_SUFFIXES,
    PRESENT_SUFFIXES,
    SUKUN,
    strip_diacritics,
    strip_trailing_vowels,
)

from .arramooz_client import ArramoozClient

INDEFINITE_CASE_SUFFIXES = {
    "nominative": DAMMATAN,
    "accusative": FATHATAN,
    "genitive": KASRATAN,
}

DEFINITE_CASE_SUFFIXES = {
    "nominative": DAMMA,
    "accusative": FATHA,
    "genitive": KASRA,
}


class MorphologicalGenerator:
    """Generates vocalized surface forms based on root/lemma and features."""

    def __init__(self, arramooz_client: ArramoozClient | None = None) -> None:
        """Initializes the MorphologicalGenerator."""
        self._client = arramooz_client or ArramoozClient()

    def generate_form(
        self, root: str, pos: str, constraints: dict[str, Any]
    ) -> list[str]:
        """Generates surface forms matching constraints.

        Args:
            root: The root/lemma of the word.
            pos: Part of speech ("noun", "verb", "adj", etc.).
            constraints: Morphological constraints
                        (case, gender, number, definiteness, annex).

        Returns:
            List of generated vocalized surface forms.
        """
        logger.debug(
            "MorphologicalGenerator.generate_form | root={} pos={} constraints={}",
            root,
            pos,
            constraints,
        )

        lemma = constraints.get("lemma") or root
        lemma = strip_diacritics(lemma)
        entries = []

        if pos in ("noun", "adj"):
            entries = self._client.get_word_by_lemma(
                lemma, "nouns"
            ) or self._client.get_words_by_root(root, "nouns")
        elif pos == "verb":
            entries = self._client.get_word_by_lemma(
                lemma, "verbs"
            ) or self._client.get_words_by_root(root, "verbs")
        else:
            entries = self._client.get_word_by_lemma(
                lemma
            ) or self._client.get_words_by_root(root)

        if not entries:
            logger.warning(
                "No entries found in dictionary for root '{}' lemma '{}'", root, lemma
            )
            return []

        results: list[str] = []
        for entry in entries:
            table = entry.get("table", "nouns")
            if table == "verbs" or pos == "verb":
                form = self._inflect_verb(entry, constraints)
            else:
                form = self._inflect_noun(entry, constraints)

            if form:
                results.append(form)

        return list(dict.fromkeys(results))

    def _inflect_noun(
        self, entry: dict[str, Any], constraints: dict[str, Any]
    ) -> str | None:
        """Applies noun inflection rules to a dictionary entry."""
        base_vocalized = entry.get("vocalized")
        if not base_vocalized:
            return None

        case = constraints.get("case") or "nominative"
        number = constraints.get("number") or "singular"
        gender = constraints.get("gender")
        if not gender:
            gender = "feminine" if entry.get("gender") == "مؤنث" else "masculine"
        annexed = constraints.get("annex", False)
        definiteness = constraints.get("definiteness") or "indefinite"
        prefix = constraints.get("prefix", "")

        stem = strip_trailing_vowels(base_vocalized)

        if gender == "feminine" and not stem.endswith("ة"):
            if entry.get("feminable") == 1:
                stem = stem + FATHA + "ة"

        # Apply dual, plural, or singular suffixes
        inflected = ""
        if number == "dual":
            if stem.endswith("ة"):
                stem_without_ta = stem[:-1] + FATHA + "ت"
            else:
                stem_without_ta = stem + FATHA

            if case == "nominative":
                suffix = "ا" if annexed else "ان"
            else:
                suffix = "ي" if annexed else "يْن"
            inflected = stem_without_ta + suffix

        elif number == "plural":
            broken = entry.get("broken_plural")
            if broken and broken.strip():
                bp_stem = strip_trailing_vowels(broken)
                inflected = self._apply_singular_ending(bp_stem, case, definiteness)
            else:
                if gender == "feminine":
                    stem_without_ta = stem
                    if stem_without_ta.endswith("ة"):
                        stem_without_ta = stem_without_ta[:-1]
                    inflected = stem_without_ta + FATHA + "ات"
                else:
                    if annexed:
                        suffix = (
                            (DAMMA + "و") if case == "nominative" else (KASRA + "ي")
                        )
                    else:
                        suffix = (
                            (DAMMA + "ون") if case == "nominative" else (KASRA + "ين")
                        ) + FATHA
                    inflected = stem + suffix
        else:
            inflected = self._apply_singular_ending(stem, case, definiteness)

        # Re-attach prefixes
        if (
            definiteness == "definite"
            and not prefix.endswith("ال")
            and not inflected.startswith("ال")
        ):
            if prefix in ("ب", "ف", "و", "ك", "ل"):
                if prefix == "ل":
                    prefix = "لل"
                else:
                    prefix = prefix + "ال"
            else:
                prefix = "ال"
        elif annexed and prefix.endswith("ال"):
            prefix = prefix[:-2]

        return prefix + inflected

    def _apply_singular_ending(self, stem: str, case: str, definiteness: str) -> str:
        """Applies case endings for singular nouns and broken plurals."""
        suffix = (
            INDEFINITE_CASE_SUFFIXES[case]
            if definiteness == "indefinite"
            else DEFINITE_CASE_SUFFIXES[case]
        )
        if (
            case == "accusative"
            and definiteness == "indefinite"
            and not stem.endswith("ة")
        ):
            suffix += "ا"
        return stem + suffix

    def _inflect_verb(
        self, entry: dict[str, Any], constraints: dict[str, Any]
    ) -> str | None:
        """Applies verb inflection rules using the original token as reference."""
        original = entry.get("vocalized")
        if not original:
            return None

        tense = constraints.get("tense", "past")
        target_number = constraints.get("number", "singular")
        target_gender = constraints.get("gender", "masculine")

        clean_form = strip_diacritics(original)
        stem = original

        if tense == "past":
            for suffix in PAST_SUFFIXES:
                if clean_form.endswith(suffix) and original.endswith(suffix):
                    stem = original[: -len(suffix)]
                    break

            stem = strip_trailing_vowels(stem)

            if target_number == "singular":
                stem += FATHA
                if target_gender == "masculine":
                    return stem
                return stem + "ت"
            elif target_number == "plural":
                if target_gender == "masculine":
                    return stem + DAMMA + "وا"
                else:
                    return stem + SUKUN + "ن" + FATHA
            return stem
        else:
            stem_with_prefix = original
            for suffix in PRESENT_SUFFIXES:
                if clean_form.endswith(suffix) and original.endswith(suffix):
                    stem_with_prefix = original[: -len(suffix)]
                    break

            clean_swp = strip_diacritics(stem_with_prefix)
            if (
                clean_swp.startswith("ي")
                or clean_swp.startswith("ت")
                or clean_swp.startswith("ن")
                or clean_swp.startswith("أ")
            ):
                stem = stem_with_prefix[1:]
                if stem and stem[0] in (FATHA, DAMMA, KASRA, SUKUN):
                    stem = stem[1:]
            else:
                stem = stem_with_prefix

            if target_gender == "masculine":
                new_prefix = "ي"
            else:
                new_prefix = "ت"

            if target_number == "singular":
                return new_prefix + stem + DAMMA
            elif target_number == "plural":
                if target_gender == "masculine":
                    return new_prefix + stem + DAMMA + "ون" + FATHA
                else:
                    return new_prefix + stem + SUKUN + "ن" + FATHA
            return original
