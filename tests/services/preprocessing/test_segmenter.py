"""Tests for the segmenter in the preprocessing service.

Each test uses the public *segment()* function and verifies the returned
Token list for correctness of form, span, norm_span, and affix_structure.
"""

from src.services.preprocessing.features.segmenter import (
    _build_affix_structure,
    break_token,
    segment,
)
from src.services.preprocessing.utils.normalizer import normalize_with_mapping

#############################################################################
# Unit tests for _build_affix_structure (pure, no Farasa needed)
#############################################################################


def test_build_affix_structure_stem_only():
    """A simple word with no clitics should produce STEM."""
    assert _build_affix_structure("ذهب") == "STEM"


def test_build_affix_structure_det_stem():
    """Definite article prefix should produce DET+STEM."""
    assert _build_affix_structure("ال+طلاب") == "DET+STEM"


def test_build_affix_structure_conj_prep_det_stem():
    """Multiple prefix clitics should all be tagged in order."""
    assert _build_affix_structure("و+ب+ال+مدرسة") == "CONJ+PREP+DET+STEM"


def test_build_affix_structure_stem_pron():
    """Pronoun suffix segment should produce STEM+PRON.

    Some examples are correctly segmented and their build affix structure is correct
    but there are other examples where FARASA doesn't segment the input even though
    it should be segmented like "كتبوه" here it should be "كتب" + "و" + "ه" but
    it is not, so we treat it all as a STEM.
    """
    assert _build_affix_structure("كتب+ها") == "STEM+PRON"
    assert _build_affix_structure("كتبوه") == "STEM"


def test_build_affix_structure_conj_stem_pron():
    """Conjunction prefix + pronoun suffix should produce CONJ+STEM+PRON."""
    assert _build_affix_structure("و+كتب+ها") == "CONJ+STEM+PRON"


def test_build_affix_structure_ta_suffix():
    """(Farasa: كتب+ت) should produce STEM+PRON."""
    assert _build_affix_structure("كتب+ت") == "STEM+PRON"


def test_build_affix_structure_multi_suffix():
    """Two adjacent suffix clitics should both be tagged PRON in order."""
    assert _build_affix_structure("ضرب+ت+هم") == "STEM+PRON+PRON"


def test_build_affix_structure_feminine_stem_not_split():
    """Farasa over-segments feminine nouns (مدرس+ة), so we don't split on 'ة'."""
    print(_build_affix_structure("و+ب+ال+مدرس+ة"))
    assert _build_affix_structure("و+ب+ال+مدرس+ة") == "CONJ+PREP+DET+STEM"


def test_build_affix_structure_punctuation():
    """Punctuation tokens contain no Arabic letters and should return None."""
    assert _build_affix_structure("،") is None
    assert _build_affix_structure(".") is None
    assert _build_affix_structure("!") is None


#############################################################################
# Integration tests for segment() — require Farasa / Java
#############################################################################


def test_segment_empty():
    """Empty or whitespace-only input should return an empty token list."""
    assert segment("", [0]) == []
    assert segment("   ", [0, 1, 2, 3]) == []


def test_segment_single_simple_word():
    """A single word with no clitics should yield one STEM token."""
    text = "ذهب"
    normalized, mapping = normalize_with_mapping(text)
    tokens = segment(normalized, mapping)

    assert len(tokens) == 1
    t = tokens[0]
    assert t.index == 0
    assert t.form == "ذهب"
    assert t.norm_span == (0, 3)
    assert t.span == (0, 3)
    assert t.affix_structure == "STEM"


def test_segment_definite_noun():
    """A noun with definite article should yield one DET+STEM token."""
    text = "الطلاب"
    normalized, mapping = normalize_with_mapping(text)
    tokens = segment(normalized, mapping)

    assert len(tokens) == 1
    t = tokens[0]
    assert t.form == "الطلاب"
    assert t.affix_structure == "DET+STEM"


def test_segment_multi_clitic_word():
    """Test segmentation of a multi-clitic word.

    A word with conjunction + preposition + definite article should produce
    CONJ+PREP+DET+STEM.
    """
    text = "وبالمدرسة"
    normalized, mapping = normalize_with_mapping(text)
    tokens = segment(normalized, mapping)

    assert len(tokens) == 1
    t = tokens[0]
    assert t.form == "وبالمدرسة"
    assert t.affix_structure == "CONJ+PREP+DET+STEM"


def test_segment_sentence_with_punctuation_and_extra_spaces():
    """Punctuation should produce its own token with affix_structure=None."""
    text = "ذهب   الطلاب، إلى"
    normalized, mapping = normalize_with_mapping(text)
    tokens = segment(normalized, mapping)

    assert len(tokens) == 4

    forms = [t.form for t in tokens]
    assert forms == ["ذهب", "الطلاب", "،", "إلى"]

    assert tokens[0].affix_structure == "STEM"
    assert tokens[1].affix_structure == "DET+STEM"
    assert tokens[2].affix_structure is None
    assert tokens[3].affix_structure == "STEM"


def test_segment_span_correctness():
    """Token spans should correctly reference positions in the normalized text."""
    text = "ذهب الطلاب"
    normalized, mapping = normalize_with_mapping(text)
    tokens = segment(normalized, mapping)

    assert len(tokens) == 2

    t0, t1 = tokens
    # verify form matches slice of normalized text.
    assert normalized[t0.norm_span[0] : t0.norm_span[1]] == t0.form
    assert normalized[t1.norm_span[0] : t1.norm_span[1]] == t1.form


def test_segment_orig_span_via_mapping():
    """Original text spans should be derivable from norm_to_orig_map."""
    # use a raw text with extra spaces so norm and orig spans differ.
    raw = "ذهب  الطلاب"  # two spaces between words
    normalized, mapping = normalize_with_mapping(raw)
    tokens = segment(normalized, mapping)

    assert len(tokens) == 2

    t0, t1 = tokens
    # orig_start of second token should skip the two spaces (index 5 in raw).
    assert raw[t0.span[0] : t0.span[1]] == "ذهب"
    assert raw[t1.span[0] : t1.span[1]] == "الطلاب"


def test_segment_token_indices_are_sequential():
    """Token index field should be a zero-based sequential counter."""
    text = "ذهب الطلاب، إلى المدرسة"
    normalized, mapping = normalize_with_mapping(text)
    tokens = segment(normalized, mapping)

    for expected_idx, token in enumerate(tokens):
        assert token.index == expected_idx


def test_segment_implicit_corrections():
    """Ensure Farasa's internal spelling corrections don't overwrite user input."""
    # Farasa internally corrects "اكرم" -> "أكرم" and "مدرسه" -> "مدرسة"
    text = "اكرم في مدرسه"
    normalized, mapping = normalize_with_mapping(text)
    tokens = segment(normalized, mapping)

    assert tokens[0].form == "اكرم"
    assert tokens[0].farasa_segmentation == "اكرم"  # Preserved missing hamza

    assert tokens[2].form == "مدرسه"
    assert (
        tokens[2].farasa_segmentation == "مدرس+ه"
    )  # Preserved haa instead of taa marbuta


def test_segment_numbers_attached():
    """Ensure words attached to numbers are kept as a single token."""
    text = "اكرم100"
    normalized, mapping = normalize_with_mapping(text)
    tokens = segment(normalized, mapping)

    assert len(tokens) == 1
    assert tokens[0].form == "اكرم100"
    assert tokens[0].farasa_segmentation == "اكرم 100"  # Joined parts
    assert tokens[0].affix_structure is None  # Invalid joined word


def test_segment_integration_original_issue():
    """Ensure the original issues reported in chat are perfectly solved."""
    text = "هذا امير اكرم100 لالله لله للحج."
    normalized, mapping = normalize_with_mapping(text)
    tokens = segment(normalized, mapping)

    assert len(tokens) == 7

    # "هذا" is unchanged
    assert tokens[0].form == "هذا"
    assert tokens[0].farasa_segmentation == "هذا"

    # "امير" remains "امير" despite Farasa correcting to "أمير"
    assert tokens[1].form == "امير"
    assert tokens[1].farasa_segmentation == "امير"

    # "اكرم100" remains merged and invalid
    assert tokens[2].form == "اكرم100"
    assert tokens[2].farasa_segmentation == "اكرم 100"
    assert tokens[2].affix_structure is None

    # "لالله"
    assert tokens[3].form == "لالله"
    assert tokens[3].farasa_segmentation == "ل+الله"

    # "لله"
    assert tokens[4].form == "لله"
    assert tokens[4].farasa_segmentation == "ل+الله"

    # "للحج" accurately maps user characters over Farasa's "ل+ال+حج"
    assert tokens[5].form == "للحج"
    assert tokens[5].farasa_segmentation == "ل+ال+حج"
    assert tokens[5].affix_structure == "PREP+DET+STEM"

    # Punctuation
    assert tokens[6].form == "."
    assert tokens[6].farasa_segmentation == "."
    assert tokens[6].affix_structure is None


def test_segment_with_tashkeel():
    """Ensure Arabic diacritics (tashkeel) do not break word boundaries."""
    text = "ذهب أمير الى المنَزل."
    normalized, mapping = normalize_with_mapping(text)
    tokens = segment(normalized, mapping)

    assert len(tokens) == 5
    assert tokens[3].form == "المنَزل"
    assert tokens[3].farasa_segmentation == "ال+منَزل"
    assert tokens[4].form == "."


def test_segment_dropped_tashkeel_with_clitics():
    """Ensure dropped tashkeel by Farasa is safely attached before the + boundary."""
    text = "لَأكلها."
    normalized, mapping = normalize_with_mapping(text)
    tokens = segment(normalized, mapping)

    assert len(tokens) == 2
    assert tokens[0].form == "لَأكلها"
    assert tokens[0].farasa_segmentation == "لَ+أكل+ها"
    assert tokens[1].form == "."


def test_text_contains_Alif():
    """Test input with alif in words."""
    text = "اكرم"
    normalized, mapping = normalize_with_mapping(text)
    tokens = segment(normalized, mapping)

    assert len(tokens) == 1
    assert tokens[0].form == "اكرم"
    assert tokens[0].farasa_segmentation == "اكرم"


#############################################################################
# Unit tests for break_token()
#############################################################################


def _make_token(
    form: str, affix_structure: str | None, farasa_segmentation: str | None = None
) -> object:
    """Creates a token."""
    from src.core.schemas import Token

    return Token(
        index=0,
        form=form,
        span=(0, len(form)),
        norm_span=(0, len(form)),
        affix_structure=affix_structure,
        farasa_segmentation=farasa_segmentation,
    )


def test_decompose_none_affix_structure():
    """Test that decompose return none when affix_structure is none."""
    assert break_token(_make_token("،", None, None)) is None


def test_decompose_stem_only():
    """Test decompose with stem only."""
    assert break_token(_make_token("ذهب", "STEM", "ذهب")) == [("STEM", "ذهب")]


def test_decompose_det_stem():
    """Test decompose with det + stem."""
    assert break_token(_make_token("الطلاب", "DET+STEM", "ال+طلاب")) == [
        ("DET", "ال"),
        ("STEM", "طلاب"),
    ]


def test_decompose_conj_prep_det_stem():
    """Test decompose with CONJ + PREP + DET + STEM."""
    result = break_token(
        _make_token("وبالمدرسة", "CONJ+PREP+DET+STEM", "و+ب+ال+مدرس+ة")
    )
    assert result == [("CONJ", "و"), ("PREP", "ب"), ("DET", "ال"), ("STEM", "مدرسة")]


def test_decompose_stem_pron():
    """Test decompose with STEM + PRON."""
    assert break_token(_make_token("كتبها", "STEM+PRON", "كتب+ها")) == [
        ("STEM", "كتب"),
        ("PRON", "ها"),
    ]


def test_decompose_conj_stem_pron():
    """Test decompose with CONJ + STEM + PRON."""
    result = break_token(_make_token("وكتبها", "CONJ+STEM+PRON", "و+كتب+ها"))
    assert result == [("CONJ", "و"), ("STEM", "كتب"), ("PRON", "ها")]


def test_decompose_repeated_pron_suffix():
    """Test decompose with STEM + PRON + PRON."""
    result = break_token(_make_token("ضربتهم", "STEM+PRON+PRON", "ضرب+ت+هم"))
    assert result == [("STEM", "ضرب"), ("PRON", "ت"), ("PRON", "هم")]


def test_decompose_result_concatenates_to_farasa_segmentation():
    """Test decompose with concatenates to farasa_segmentation without '+'."""
    token = _make_token("وبالمدرسة", "CONJ+PREP+DET+STEM", "و+ب+ال+مدرس+ة")
    result = break_token(token)
    assert "".join(v for _, v in result) == token.farasa_segmentation.replace("+", "")
