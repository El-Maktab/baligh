"""Tests for the morphological analyzer in the preprocessing service."""

from src.core.schemas import Token
from src.services.preprocessing.features.analyzer import (
    _map_analysis,
    analyze,
)

#############################################################################
# Helpers
#############################################################################


def _make_token(index: int, form: str, affix_structure: str | None = "STEM") -> Token:
    """Builds a minimal Token for testing."""
    return Token(
        index=index,
        form=form,
        span=(0, len(form)),
        norm_span=(0, len(form)),
        affix_structure=affix_structure,
    )


#############################################################################
# Unit tests for _map_analysis (no CAMeL models needed)
#############################################################################


def test_map_analysis_verb():
    """A verb analysis dict should map to the correct MorphAnalysis fields."""
    camel_dict = {
        "lex": "ذَهَب",
        "pos": "verb",
        "gen": "m",
        "num": "s",
        "per": "3",
        "cas": "na",
        "vox": "a",
        "mod": "i",
        "asp": "p",
        "diac": "ذَهَبَ",
        "stt": "na",
    }
    result = _map_analysis(camel_dict, token_index=0, is_disambiguated=True)

    assert result.token_index == 0
    assert result.lemma == "ذَهَب"
    assert result.pos == "VERB"
    assert result.gender == "masculine"
    assert result.number == "singular"
    assert result.person == "third"
    assert result.tense == "past"
    assert result.voice == "active"
    assert result.mood == "indicative"
    assert result.diacritized == "ذَهَبَ"
    assert result.is_disambiguated is True


def test_map_analysis_noun():
    """A noun analysis dict should map correctly including definiteness and case."""
    camel_dict = {
        "lex": "طالِب",
        "pos": "noun",
        "gen": "m",
        "num": "p",
        "per": "na",
        "cas": "g",
        "vox": "na",
        "mod": "na",
        "asp": "na",
        "diac": "الطُلّابِ",
        "stt": "d",
    }
    result = _map_analysis(camel_dict, token_index=1, is_disambiguated=False)

    assert result.pos == "NOUN"
    assert result.gender == "masculine"
    assert result.number == "plural"
    assert result.person is None
    assert result.case == "genitive"
    assert result.definiteness == "definite"
    assert result.tense is None
    assert result.lemma == "طالِب"
    assert result.diacritized == "الطُلّابِ"
    assert result.is_disambiguated is False


def test_map_analysis_punctuation():
    """Punctuation analysis should have pos=PUNC, lemma=None, diacritized=None."""
    camel_dict = {
        "lex": "،",
        "pos": "punc",
        "gen": "na",
        "num": "na",
        "per": "na",
        "cas": "na",
        "vox": "na",
        "mod": "na",
        "asp": "na",
        "diac": "،",
        "stt": "na",
    }
    result = _map_analysis(camel_dict, token_index=2, is_disambiguated=True)

    assert result.pos == "PUNC"
    assert result.lemma is None
    assert result.diacritized is None
    assert result.gender is None
    assert result.is_disambiguated is True


def test_map_analysis_undefined_case_is_none():
    """CAMeL case='u' (undefined) should map to None."""
    camel_dict = {
        "lex": "ذَهَب",
        "pos": "noun",
        "gen": "m",
        "num": "s",
        "per": "na",
        "cas": "u",
        "vox": "na",
        "mod": "na",
        "asp": "na",
        "diac": "ذَهَب",
        "stt": "i",
    }
    result = _map_analysis(camel_dict, token_index=0, is_disambiguated=False)
    assert result.case is None
    assert result.definiteness == "indefinite"


def test_map_analysis_noun_prop_maps_to_noun_prop():
    """CAMeL noun_prop POS should map to our distinct NOUN_PROP tag."""
    camel_dict = {
        "lex": "ذَهَب",
        "pos": "noun_prop",
        "gen": "f",
        "num": "s",
        "per": "na",
        "cas": "u",
        "vox": "na",
        "mod": "na",
        "asp": "na",
        "diac": "ذَهَب",
        "stt": "i",
    }
    result = _map_analysis(camel_dict, token_index=0, is_disambiguated=False)
    assert result.pos == "NOUN_PROP"


#############################################################################
# Integration tests for analyze() — require CAMeL models
#############################################################################


def test_analyze_empty():
    """Empty token list should return empty list."""
    assert analyze([]) == []


def test_analyze_result_length_matches_tokens():
    """Result list length must equal token count."""
    tokens = [_make_token(0, "ذهب"), _make_token(1, "الطلاب")]
    result = analyze(tokens)
    assert len(result) == len(tokens)


def test_analyze_each_token_has_at_least_one_candidate():
    """Every token should produce at least one MorphAnalysis."""
    tokens = [
        _make_token(0, "ذهب"),
        _make_token(1, "الطلاب"),
        _make_token(2, "،", affix_structure=None),
        _make_token(3, "إلى"),
    ]
    result = analyze(tokens)
    for candidates in result:
        assert len(candidates) >= 1


def test_analyze_disambiguated_is_first():
    """Index 0 of every token's candidates must have is_disambiguated=True."""
    tokens = [_make_token(0, "ذهب"), _make_token(1, "الطلاب")]
    result = analyze(tokens)
    for candidates in result:
        assert candidates[0].is_disambiguated is True


def test_analyze_only_first_is_disambiguated():
    """Only index 0 should have is_disambiguated=True, all others False."""
    tokens = [_make_token(0, "ذهب")]
    result = analyze(tokens)
    candidates = result[0]
    assert candidates[0].is_disambiguated is True
    for c in candidates[1:]:
        assert c.is_disambiguated is False


def test_analyze_no_duplicate_analyses():
    """No two MorphAnalysis candidates for the same token should be identical."""
    tokens = [_make_token(0, "ذهب")]
    result = analyze(tokens)
    seen: set[tuple] = set()
    for c in result[0]:
        key = (
            c.lemma,
            c.pos,
            c.gender,
            c.number,
            c.person,
            c.definiteness,
            c.case,
            c.tense,
            c.voice,
            c.mood,
            c.diacritized,
        )
        assert key not in seen, f"Duplicate analysis: {key}"
        seen.add(key)


def test_analyze_token_index_correct():
    """MorphAnalysis.token_index must match the originating Token.index."""
    tokens = [_make_token(0, "ذهب"), _make_token(1, "الطلاب")]
    result = analyze(tokens)
    for token_idx, candidates in enumerate(result):
        for c in candidates:
            assert c.token_index == token_idx


def test_analyze_pos_is_uppercase_nonempty():
    """Pos field must be non-empty and uppercase for all candidates."""
    tokens = [_make_token(0, "ذهب"), _make_token(1, "الطلاب")]
    result = analyze(tokens)
    for candidates in result:
        for c in candidates:
            assert c.pos
            assert c.pos == c.pos.upper()


def test_analyze_punctuation():
    """Punctuation token should have pos=PUNC, lemma=None, diacritized=None."""
    tokens = [_make_token(0, "،", affix_structure=None)]
    result = analyze(tokens)
    punc = result[0][0]
    assert punc.pos == "PUNC"
    assert punc.lemma is None
    assert punc.diacritized is None


def test_analyze_lemma_and_diacritized_are_distinct():
    """For not-base-form words, lemma (lex) and diacritized (diac) must differ."""
    tokens = [_make_token(0, "الطلاب")]
    result = analyze(tokens)
    best = result[0][0]
    # lemma = طالِب (singular base), diacritized = الطُلّابِ (full form)
    assert best.lemma is not None
    assert best.diacritized is not None
    assert best.lemma != best.diacritized


def test_analyze_verb_fields():
    """A verb token should have tense, voice populated, gender/number from agreement."""
    tokens = [_make_token(0, "ذهب")]
    result = analyze(tokens)
    best = result[0][0]
    assert best.pos == "VERB"
    assert best.tense == "past"
    assert best.voice == "active"
    assert best.diacritized is not None


def test_analyze_oov():
    tokens = [_make_token(0, "ذهب"), _make_token(1, "الطلابب")]
    analyze(tokens)
    assert tokens[0].is_oov is False
    assert tokens[1].is_oov is True
