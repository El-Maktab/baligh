"""Morphological analysis service for Baligh preprocessing.

This module uses CAMeL Tools' morphological analyzer and MLE disambiguator
to produce MorphAnalysis candidates for each token in the completed prefix.

Design decisions:
    - The disambiguated result is always placed at index 0 with
        is_disambiguated=True. All other unique analyzer candidates follow
        with is_disambiguated=False.
    - Deduplication: We skip the disambiguated value from the results of the analyzer
        if it is generated again by it. The match key is (diac, pos, lex) which
        should be distinctive within one word.
    - CAMeL's lex field maps to our lemma (base/dictionary form).
        CAMeL's diac field maps to our diacritized (fully diacritized
        surface form of the token). They are always distinct for inflected words.
    - Punctuation tokens (CAMeL pos=punc) receive lemma=None and
        diacritized=None per the contract.
    - Both CAMeL singletons use double-checked locking for thread safety.

References:
- docs/contracts/preprocessing-contract.md

Authors:
    - Akram Hany
"""

import threading
from typing import TYPE_CHECKING

from src.core.schemas import MorphAnalysis, Token

if TYPE_CHECKING:
    from camel_tools.disambig.mle import MLEDisambiguator
    from camel_tools.morphology.analyzer import Analyzer

#############################################################################
# Lazy singletons.
#############################################################################

_analyzer: "Analyzer | None" = None
_analyzer_lock = threading.Lock()

_disambiguator: "MLEDisambiguator | None" = None
_disambiguator_lock = threading.Lock()


def _get_analyzer() -> "Analyzer":
    """Returns the shared Analyzer instance, initialising it if needed.

    Uses double-checked locking so only one thread create the object.

    Returns:
        The process-wide Analyzer backed by the built-in MorphologyDB.
    """
    global _analyzer
    if _analyzer is None:
        with _analyzer_lock:
            if _analyzer is None:
                from camel_tools.morphology.analyzer import Analyzer
                from camel_tools.morphology.database import MorphologyDB

                db = MorphologyDB.builtin_db()
                _analyzer = Analyzer(db)
    return _analyzer


def _get_disambiguator() -> "MLEDisambiguator":
    """Returns the shared MLEDisambiguator instance, initialising it if needed.

    Uses double-checked locking so only one thread create the object.

    Returns:
        The process-wide MLEDisambiguator loaded with the pre-trained model.
    """
    global _disambiguator
    if _disambiguator is None:
        with _disambiguator_lock:
            if _disambiguator is None:
                from camel_tools.disambig.mle import MLEDisambiguator

                _disambiguator = MLEDisambiguator.pretrained()
    return _disambiguator


#############################################################################
# Tag mapping tables (CAMeL abbreviated values -> our human-readable schema)
#############################################################################

# CAMeL POS tags that have no direct equivalent default to uppercase raw value.
_POS_MAP: dict[str, str] = {
    # Noun: General noun (ex. كتاب، شجرة)
    "noun": "NOUN",
    # Proper Noun: Names of people, places, or entities (ex. محمد، القاهرة)
    "noun_prop": "NOUN_PROP",
    # Quantifier Noun: Words indicating quantity (ex. كل، بعض، جميع)
    "noun_quant": "NOUN_QUANT",
    # Abbreviation: Shortened form of a word or phrase (ex. إلخ، د.)
    "abbrev": "NOUN",
    # Verb: Action or state words (ex. كتب، يقرأ، اسمع)
    "verb": "VERB",
    # Adjective: Describing words (ex. جميل، كبير)
    "adj": "ADJ",
    # Adverb: Words modifying verbs, adjectives, or other adverbs (ex. غداً، أمس، جداً)
    "adv": "ADV",
    # Preposition: Relation-showing words (ex. في، من، إلى، على)
    "prep": "PREP",
    # Conjunction: Connecting words (ex. و، فـ، ثم، أو)
    "conj": "CONJ",
    # Pronoun: Personal, possessive, or demonstrative pronouns (ex. هو، هي، هذا)
    "pron": "PRON",
    # Interrogative Pronoun: Question-asking pronouns (ex. من، ما، أين)
    "pron_interrog": "PRON_INTERROG",
    # Relative Pronoun: Pronouns referring back to nouns (ex. الذي، التي، الذين)
    "pron_rel": "PRON_REL",
    # Determiner: Definite articles and similar markers (ex. الـ)
    "det": "DET",
    # Particle: Grammatical particles like negation, vocative, etc. (ex. لم، لن، يا)
    "part": "PART",
    # Punctuation: Standard punctuation marks (ex. .، ،، ؟، !)
    "punc": "PUNC",
    # Digit: Numerical values and digits (ex. 1، 2، 3)
    "digit": "NUM",
    # Interjection: Words expressing emotion or exclamation (ex. آه، واه)
    "interj": "INTJ",
}

_GEN_MAP: dict[str, str | None] = {
    "m": "masculine",
    "f": "feminine",
    # Not applicable gender (ex. punctuation or particles)
    "na": None,
    # Undetermined or unspecified gender
    "u": None,
}

_NUM_MAP: dict[str, str | None] = {
    "s": "singular",
    "d": "dual",
    "p": "plural",
    # Not applicable grammatical number
    "na": None,
    # Undetermined grammatical number
    "u": None,
}

_PER_MAP: dict[str, str | None] = {
    # (I/we)
    "1": "first",
    # (you)
    "2": "second",
    # (he/she/they)
    "3": "third",
    # Not applicable grammatical person
    "na": None,
    # Undetermined grammatical person
    "u": None,
}

_CAS_MAP: dict[str, str | None] = {
    # (Marfu')
    "n": "nominative",
    # (Mansoub)
    "a": "accusative",
    # (Majrour)
    "g": "genitive",
    # Undetermined grammatical case
    "u": None,
    # Not applicable grammatical case
    "na": None,
}

_VOX_MAP: dict[str, str | None] = {
    # Active (Ma'rouf)
    "a": "active",
    # Passive (Majhool)
    "p": "passive",
    # Not applicable voice
    "na": None,
}

_MOD_MAP: dict[str, str | None] = {
    # (Marfu' for verbs)
    "i": "indicative",
    # (Mansoub for verbs)
    "s": "subjunctive",
    # (Majzoum for verbs)
    "j": "jussive",
    # Not applicable grammatical mood
    "na": None,
    # Undetermined grammatical mood
    "u": None,
}

# (aspect is tense).
_ASP_MAP: dict[str, str | None] = {
    # Past tense (Madi)
    "p": "past",
    # Present/Future tense (Mudari')
    "i": "present",
    # Imperative mood/tense (Amr)
    "c": "imperative",
    # Not applicable tense/aspect
    "na": None,
}

_STT_MAP: dict[str, str | None] = {
    # (Ma'rifah, ex. with Al-)
    "d": "definite",
    # (Nakirah, ex. with Tanween)
    "i": "indefinite",
    # Construct state (Idafah context)
    "c": None,
    # Not applicable state
    "na": None,
    # Undetermined state
    "u": None,
}


#############################################################################
# Internal helpers
#############################################################################


def _map_analysis(
    camel_dict: dict,
    token_index: int,
    is_disambiguated: bool,
) -> MorphAnalysis:
    """Converts a raw CAMeL analysis dict into a MorphAnalysis object.

    Args:
        camel_dict: A dict produced by CAMeL's Analyzer.analyze() or taken
            from ScoredAnalysis.analysis inside a DisambiguatedWord.
        token_index: Index of the Token this analysis belongs to.
        is_disambiguated: True if this is the MLEDisambiguator's selected
            candidate for the token.

    Returns:
        A MorphAnalysis with all fields mapped from CAMeL's abbreviated values
        to the human-readable values defined in the contract.
    """
    pos_raw = camel_dict.get("pos", "")
    pos = _POS_MAP.get(pos_raw, pos_raw.upper())
    is_punc = pos == "PUNC"

    return MorphAnalysis(
        token_index=token_index,
        lemma=None if is_punc else (camel_dict.get("lex") or None),
        pos=pos,
        gender=_GEN_MAP.get(camel_dict.get("gen", "na")),
        number=_NUM_MAP.get(camel_dict.get("num", "na")),
        person=_PER_MAP.get(camel_dict.get("per", "na")),
        definiteness=_STT_MAP.get(camel_dict.get("stt", "na")),
        case=_CAS_MAP.get(camel_dict.get("cas", "na")),
        tense=_ASP_MAP.get(camel_dict.get("asp", "na")),
        voice=_VOX_MAP.get(camel_dict.get("vox", "na")),
        mood=_MOD_MAP.get(camel_dict.get("mod", "na")),
        diacritized=None if is_punc else (camel_dict.get("diac") or None),
        is_disambiguated=is_disambiguated,
    )


#############################################################################
# Public API
#############################################################################


def analyze(tokens: list[Token]) -> list[list[MorphAnalysis]]:
    """Runs morphological analysis and disambiguation on a list of tokens.

    For each token, produces a list of MorphAnalysis candidates where:

    - Index 0 is always the MLEDisambiguator's selected candidate
        (is_disambiguated=True).
    - All remaining candidates are the full Analyzer output with the
        disambiguated one removed to prevent duplication
        (is_disambiguated=False).

    Fallbacks:
    - If the disambiguator returns no analyses for a token (unknown word),
        all analyzer candidates are returned with is_disambiguated=False.
    - If the analyzer also returns nothing, only the disambiguated result
        is returned as a single-element list.

    Args:
        tokens: List of Token objects produced by the segmentation phase.
            Token forms must already be normalized.

    Returns:
        A list of the same length as tokens, where each element is a
        non-empty list of MorphAnalysis candidates for that token.
    """
    if not tokens:
        return []

    forms = [t.form for t in tokens]
    ana = _get_analyzer()
    dis = _get_disambiguator()

    disambig_results = dis.disambiguate(forms)

    output: list[list[MorphAnalysis]] = []

    for token, dw in zip(tokens, disambig_results, strict=False):
        disambig_dict: dict | None = dw.analyses[0].analysis if dw.analyses else None
        all_candidates: list[dict] = ana.analyze(token.form)

        candidates: list[MorphAnalysis] = []

        if disambig_dict is not None:
            # Index 0: the disambiguated best candidate.
            candidates.append(_map_analysis(disambig_dict, token.index, True))

        # add all analyzer values. any value that is identical to the
        # disambiguated one will be filtered out below.
        for c in all_candidates:
            candidates.append(_map_analysis(c, token.index, False))

        # Final deduplication at the mapped-schema level, it is used to make
        # sure that no 2 entries in candidates have the same identical values.
        seen: set[tuple] = set()
        deduped: list[MorphAnalysis] = []
        for ma in candidates:
            key = (
                ma.lemma,
                ma.pos,
                ma.gender,
                ma.number,
                ma.person,
                ma.definiteness,
                ma.case,
                ma.tense,
                ma.voice,
                ma.mood,
                ma.diacritized,
            )
            if key not in seen:
                seen.add(key)
                deduped.append(ma)
        candidates = deduped

        output.append(candidates)

    return output
