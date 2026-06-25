"""Mock Preprocessing Service.

used for testing the GEDService in isolation from the actual preprocessing pipeline.
NOTE: that it can be used to test other services as well.

Each fixture is stored under a short slug with four fields:
- label: short description of the case
- error_category: GED category under test
- has_error: whether the sentence contains an error
- input: a ready-to-use `GEDInput` for `GEDService`

Example:
```python
    from tests.mocks.mock_preprocessing import FIXTURES, _make_ged_input

    for slug, fixture in FIXTURES.items():
        output = ged_service.process(fixture["input"])

    # When testing you might want to add something like this
    # it will run your test on every fixture
    @pytest.mark.parametrize("slug", FIXTURES.keys())
```

Authors:
    Amir Anwar
"""

from src.core.schemas import MorphAnalysis, Token
from src.services.ged.schemas import GEDInput

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_ged_input(
    text: str,
    tokens: list[Token],
    morph_features: list[list[MorphAnalysis]],
    normalized_text: str | None = None,
) -> GEDInput:
    """Build a GEDInput object."""
    return GEDInput(
        text=text,
        normalized_text=normalized_text if normalized_text is not None else text,
        tokens=tokens,
        morph_features=morph_features,
    )


# ---------------------------------------------------------------------------
# Fixture registry
# The key is a short slug used as a pytest ID.
# ---------------------------------------------------------------------------

FIXTURES: dict[str, dict] = {}


def _reg(
    slug: str, label: str, error_category: str, has_error: bool, ged_input: GEDInput
) -> None:
    """Register a fixture into the FIXTURES dict."""
    FIXTURES[slug] = {
        "label": label,
        "error_category": error_category,
        "has_error": has_error,
        "input": ged_input,
    }


# ===========================================================================
# ORTHOGRAPHY (OT) : Hamza of Cut vs Connection
# ===========================================================================

_reg(
    "ot_hamza_prep_missing_correct",
    label="حرف الجر 'إلى' : همزة القطع مكتوبة بشكل صحيح",
    error_category="OT",
    has_error=False,
    ged_input=_make_ged_input(
        text="ذهب إلى المدرسة",
        tokens=[
            Token(index=0, form="ذهب", span=(0, 3), norm_span=(0, 3)),
            Token(index=1, form="إلى", span=(4, 7), norm_span=(4, 7)),
            Token(
                index=2,
                form="المدرسة",
                span=(8, 15),
                norm_span=(8, 15),
            ),
        ],
        morph_features=[
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="ذهب",
                    pos="VERB",
                    gender="masculine",
                    number="singular",
                    person="third",
                    tense="past",
                    voice="active",
                    diacritized="ذَهَبَ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="إلى",
                    pos="PREP",
                    diacritized="إِلَى",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=2,
                    lemma="مدرسة",
                    pos="NOUN",
                    gender="feminine",
                    number="singular",
                    definiteness="definite",
                    case="genitive",
                    diacritized="الْمَدْرَسَةِ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

_reg(
    "ot_hamza_prep_bare_alif_error",
    label="حرف الجر مكتوب 'الى' بألف مجردة : خطأ في حذف همزة القطع",
    error_category="OT",
    has_error=True,
    ged_input=_make_ged_input(
        text="ذهب الى المدرسة",
        tokens=[
            Token(index=0, form="ذهب", span=(0, 3), norm_span=(0, 3)),
            Token(index=1, form="الى", span=(4, 7), norm_span=(4, 7)),
            Token(
                index=2,
                form="المدرسة",
                span=(8, 15),
                norm_span=(8, 15),
            ),
        ],
        morph_features=[
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="ذهب",
                    pos="VERB",
                    gender="masculine",
                    number="singular",
                    person="third",
                    tense="past",
                    voice="active",
                    diacritized="ذَهَبَ",
                    is_disambiguated=True,
                )
            ],
            # NOTE: The preprocessor still resolves it as PREP through the lemma.
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="إلى",
                    pos="PREP",
                    diacritized="إِلَى",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=2,
                    lemma="مدرسة",
                    pos="NOUN",
                    gender="feminine",
                    number="singular",
                    definiteness="definite",
                    case="genitive",
                    diacritized="الْمَدْرَسَةِ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

# ===========================================================================
# ORTHOGRAPHY (OT) : Ta Marbuta vs Ha
# ===========================================================================

_reg(
    "ot_ta_marbuta_feminine_noun_correct",
    label="اسم مؤنث ينتهي بتاء مربوطة ة : صحيح",
    error_category="OT",
    has_error=False,
    ged_input=_make_ged_input(
        text="المدرسة كبيرة",
        tokens=[
            Token(index=0, form="المدرسة", span=(0, 7), norm_span=(0, 7)),
            Token(index=1, form="كبيرة", span=(8, 13), norm_span=(8, 13)),
        ],
        morph_features=[
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="مدرسة",
                    pos="NOUN",
                    gender="feminine",
                    number="singular",
                    definiteness="definite",
                    case="nominative",
                    diacritized="الْمَدْرَسَةُ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="كبير",
                    pos="ADJ",
                    gender="feminine",
                    number="singular",
                    definiteness="indefinite",
                    case="nominative",
                    diacritized="كَبِيرَةٌ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

_reg(
    "ot_ta_marbuta_ha_instead_of_ta_error",
    label="اسم مؤنث مكتوب بهاء ه بدلاً من تاء مربوطة ة : خطأ إملائي",
    error_category="OT",
    has_error=True,
    ged_input=_make_ged_input(
        text="المدرسه كبيرة",
        tokens=[
            Token(index=0, form="المدرسه", span=(0, 7), norm_span=(0, 7)),
            Token(index=1, form="كبيرة", span=(8, 13), norm_span=(8, 13)),
        ],
        morph_features=[
            # NOTE: preprocessing still resolves the lemma/gender correctly
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="مدرسة",
                    pos="NOUN",
                    gender="feminine",
                    number="singular",
                    definiteness="definite",
                    case="nominative",
                    diacritized="الْمَدْرَسَةُ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="كبير",
                    pos="ADJ",
                    gender="feminine",
                    number="singular",
                    definiteness="indefinite",
                    case="nominative",
                    diacritized="كَبِيرَةٌ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

# ===========================================================================
# ORTHOGRAPHY (OT) : Alif Maqsura vs Ya
# ===========================================================================

_reg(
    "ot_alif_maqsura_prep_correct",
    label="حرف الجر 'على' : ينتهي بألف مقصورة ى : صحيح",
    error_category="OT",
    has_error=False,
    ged_input=_make_ged_input(
        text="على الطاولة",
        tokens=[
            Token(index=0, form="على", span=(0, 3), norm_span=(0, 3)),
            Token(
                index=1,
                form="الطاولة",
                span=(4, 11),
                norm_span=(4, 11),
            ),
        ],
        morph_features=[
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="على",
                    pos="PREP",
                    diacritized="عَلَى",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="طاولة",
                    pos="NOUN",
                    gender="feminine",
                    number="singular",
                    definiteness="definite",
                    case="genitive",
                    diacritized="الطَّاوِلَةِ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

_reg(
    "ot_alif_maqsura_ya_instead_error",
    label="حرف الجر مكتوب 'علي' بياء ي بدلاً من ألف مقصورة ى : خطأ إملائي",
    error_category="OT",
    has_error=True,
    ged_input=_make_ged_input(
        text="علي الطاولة",
        tokens=[
            Token(index=0, form="علي", span=(0, 3), norm_span=(0, 3)),
            Token(
                index=1,
                form="الطاولة",
                span=(4, 11),
                norm_span=(4, 11),
            ),
        ],
        morph_features=[
            # NOTE: preprocessor still resolves it as PREP through the lemma.
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="على",
                    pos="PREP",
                    diacritized="عَلَى",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="طاولة",
                    pos="NOUN",
                    gender="feminine",
                    number="singular",
                    definiteness="definite",
                    case="genitive",
                    diacritized="الطَّاوِلَةِ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

# ===========================================================================
# SYNTAX (SY) : Subject-Verb agreement: VSO order
# In VSO the verb must be singular regardless of subject number.
# ===========================================================================

_reg(
    "sy_vso_verb_singular_correct",
    label="ترتيب فعل-فاعل-مفعول: الفعل مفرد قبل الفاعل الجمع : صحيح",
    error_category="SY",
    has_error=False,
    ged_input=_make_ged_input(
        text="ذهب الطلاب إلى المدرسة",
        tokens=[
            Token(index=0, form="ذهب", span=(0, 3), norm_span=(0, 3)),
            Token(index=1, form="الطلاب", span=(4, 10), norm_span=(4, 10)),
            Token(index=2, form="إلى", span=(11, 14), norm_span=(11, 14)),
            Token(
                index=3,
                form="المدرسة",
                span=(15, 22),
                norm_span=(15, 22),
            ),
        ],
        morph_features=[
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="ذهب",
                    pos="VERB",
                    gender="masculine",
                    number="singular",
                    person="third",
                    tense="past",
                    voice="active",
                    diacritized="ذَهَبَ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="طالب",
                    pos="NOUN",
                    gender="masculine",
                    number="plural",
                    definiteness="definite",
                    case="nominative",
                    diacritized="الطُّلَابُ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=2,
                    lemma="إلى",
                    pos="PREP",
                    diacritized="إِلَى",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=3,
                    lemma="مدرسة",
                    pos="NOUN",
                    gender="feminine",
                    number="singular",
                    definiteness="definite",
                    case="genitive",
                    diacritized="الْمَدْرَسَةِ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

_reg(
    "sy_vso_verb_plural_error",
    label="الفعل جمع قبل الفاعل : مخالفة قاعدة الإفراد : خطأ نحوي",
    error_category="SY",
    has_error=True,
    ged_input=_make_ged_input(
        text="ذهبوا الطلاب إلى المدرسة",
        tokens=[
            Token(index=0, form="ذهبوا", span=(0, 5), norm_span=(0, 5)),
            Token(index=1, form="الطلاب", span=(6, 12), norm_span=(6, 12)),
            Token(index=2, form="إلى", span=(13, 16), norm_span=(13, 16)),
            Token(
                index=3,
                form="المدرسة",
                span=(17, 24),
                norm_span=(17, 24),
            ),
        ],
        morph_features=[
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="ذهب",
                    pos="VERB",
                    gender="masculine",
                    number="plural",
                    person="third",
                    tense="past",
                    voice="active",
                    diacritized="ذَهَبُوا",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="طالب",
                    pos="NOUN",
                    gender="masculine",
                    number="plural",
                    definiteness="definite",
                    case="nominative",
                    diacritized="الطُّلَابُ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=2,
                    lemma="إلى",
                    pos="PREP",
                    diacritized="إِلَى",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=3,
                    lemma="مدرسة",
                    pos="NOUN",
                    gender="feminine",
                    number="singular",
                    definiteness="definite",
                    case="genitive",
                    diacritized="الْمَدْرَسَةِ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

# ===========================================================================
# SYNTAX (SY) : Subject-Verb agreement: SVO order
# In SVO the verb must agree in BOTH gender and number.
# ===========================================================================

_reg(
    "sy_svo_full_agreement_correct",
    label="ترتيب فاعل-فعل-مفعول: الفاعل يسبق الفعل مع توافق تام في العدد والجنس : صحيح",
    error_category="SY",
    has_error=False,
    ged_input=_make_ged_input(
        text="الطلاب ذهبوا إلى المدرسة",
        tokens=[
            Token(index=0, form="الطلاب", span=(0, 6), norm_span=(0, 6)),
            Token(index=1, form="ذهبوا", span=(7, 12), norm_span=(7, 12)),
            Token(index=2, form="إلى", span=(13, 16), norm_span=(13, 16)),
            Token(
                index=3,
                form="المدرسة",
                span=(17, 24),
                norm_span=(17, 24),
            ),
        ],
        morph_features=[
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="طالب",
                    pos="NOUN",
                    gender="masculine",
                    number="plural",
                    definiteness="definite",
                    case="nominative",
                    diacritized="الطُّلَابُ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="ذهب",
                    pos="VERB",
                    gender="masculine",
                    number="plural",
                    person="third",
                    tense="past",
                    voice="active",
                    diacritized="ذَهَبُوا",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=2,
                    lemma="إلى",
                    pos="PREP",
                    diacritized="إِلَى",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=3,
                    lemma="مدرسة",
                    pos="NOUN",
                    gender="feminine",
                    number="singular",
                    definiteness="definite",
                    case="genitive",
                    diacritized="الْمَدْرَسَةِ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

_reg(
    "sy_svo_gender_mismatch_error",
    label="ترتيب فاعل-فعل-مفعول: الفاعل مؤنث جمع والفعل مذكر مفرد : خطأ في المطابقة",
    error_category="SY",
    has_error=True,
    ged_input=_make_ged_input(
        text="الطالبات ذهب إلى المدرسة",
        tokens=[
            Token(index=0, form="الطالبات", span=(0, 8), norm_span=(0, 8)),
            Token(index=1, form="ذهب", span=(9, 12), norm_span=(9, 12)),
            Token(index=2, form="إلى", span=(13, 16), norm_span=(13, 16)),
            Token(
                index=3,
                form="المدرسة",
                span=(17, 24),
                norm_span=(17, 24),
            ),
        ],
        morph_features=[
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="طالبة",
                    pos="NOUN",
                    gender="feminine",
                    number="plural",
                    definiteness="definite",
                    case="nominative",
                    diacritized="الطَّالِبَاتُ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="ذهب",
                    pos="VERB",
                    gender="masculine",
                    number="singular",
                    person="third",
                    tense="past",
                    voice="active",
                    diacritized="ذَهَبَ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=2,
                    lemma="إلى",
                    pos="PREP",
                    diacritized="إِلَى",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=3,
                    lemma="مدرسة",
                    pos="NOUN",
                    gender="feminine",
                    number="singular",
                    definiteness="definite",
                    case="genitive",
                    diacritized="الْمَدْرَسَةِ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

# ===========================================================================
# SYNTAX (SY) : Noun-Adjective agreement
# ===========================================================================

_reg(
    "sy_noun_adj_agreement_correct",
    label="اسم مذكر مفرد معرفة مع نعت مطابق له : صحيح",
    error_category="SY",
    has_error=False,
    ged_input=_make_ged_input(
        text="الطالب المجتهد نجح",
        tokens=[
            Token(index=0, form="الطالب", span=(0, 6), norm_span=(0, 6)),
            Token(
                index=1,
                form="المجتهد",
                span=(7, 14),
                norm_span=(7, 14),
            ),
            Token(index=2, form="نجح", span=(15, 18), norm_span=(15, 18)),
        ],
        morph_features=[
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="طالب",
                    pos="NOUN",
                    gender="masculine",
                    number="singular",
                    definiteness="definite",
                    case="nominative",
                    diacritized="الطَّالِبُ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="مجتهد",
                    pos="ADJ",
                    gender="masculine",
                    number="singular",
                    definiteness="definite",
                    case="nominative",
                    diacritized="الْمُجْتَهِدُ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=2,
                    lemma="نجح",
                    pos="VERB",
                    gender="masculine",
                    number="singular",
                    person="third",
                    tense="past",
                    voice="active",
                    diacritized="نَجَحَ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

_reg(
    "sy_noun_adj_definiteness_mismatch_error",
    label="اسم معرفة يتبعه نعت نكرة : عدم تطابق في التعريف والتنكير : خطأ نحوي",
    error_category="SY",
    has_error=True,
    ged_input=_make_ged_input(
        text="الطالب مجتهد نجح",
        tokens=[
            Token(index=0, form="الطالب", span=(0, 6), norm_span=(0, 6)),
            Token(index=1, form="مجتهد", span=(7, 12), norm_span=(7, 12)),
            Token(index=2, form="نجح", span=(13, 16), norm_span=(13, 16)),
        ],
        morph_features=[
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="طالب",
                    pos="NOUN",
                    gender="masculine",
                    number="singular",
                    definiteness="definite",
                    case="nominative",
                    diacritized="الطَّالِبُ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="مجتهد",
                    pos="ADJ",
                    gender="masculine",
                    number="singular",
                    definiteness="indefinite",
                    case="nominative",
                    diacritized="مُجْتَهِدٌ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=2,
                    lemma="نجح",
                    pos="VERB",
                    gender="masculine",
                    number="singular",
                    person="third",
                    tense="past",
                    voice="active",
                    diacritized="نَجَحَ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

_reg(
    "sy_non_human_plural_adj_correct",
    label="جمع تكسير لغير العاقل مع نعت مؤنث مفرد : صحيح وفق قواعد العربية",
    error_category="SY",
    has_error=False,
    ged_input=_make_ged_input(
        text="كتب مفيدة",
        tokens=[
            Token(index=0, form="كتب", span=(0, 3), norm_span=(0, 3)),
            Token(index=1, form="مفيدة", span=(4, 9), norm_span=(4, 9)),
        ],
        morph_features=[
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="كتاب",
                    pos="NOUN",
                    gender="masculine",
                    number="plural",
                    definiteness="indefinite",
                    case="nominative",
                    diacritized="كُتُبٌ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="مفيد",
                    pos="ADJ",
                    gender="feminine",
                    number="singular",
                    definiteness="indefinite",
                    case="nominative",
                    diacritized="مُفِيدَةٌ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

_reg(
    "sy_non_human_plural_adj_masculine_error",
    label="جمع تكسير لغير العاقل مع نعت مذكر جمع : مخالفة قاعدة العربية : خطأ نحوي",
    error_category="SY",
    has_error=True,
    ged_input=_make_ged_input(
        text="كتب مفيدون",
        tokens=[
            Token(index=0, form="كتب", span=(0, 3), norm_span=(0, 3)),
            Token(index=1, form="مفيدون", span=(4, 10), norm_span=(4, 10)),
        ],
        morph_features=[
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="كتاب",
                    pos="NOUN",
                    gender="masculine",
                    number="plural",
                    definiteness="indefinite",
                    case="nominative",
                    diacritized="كُتُبٌ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="مفيد",
                    pos="ADJ",
                    gender="masculine",
                    number="plural",
                    definiteness="indefinite",
                    case="nominative",
                    diacritized="مُفِيدُونَ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

# ===========================================================================
# PUNCTUATION (PC) : Spacing around punctuation marks
# ===========================================================================

_reg(
    "pc_punctuation_correct_spacing",
    label="الفاصلة مباشرة بعد الكلمة ومسافة بعدها : صحيح",
    error_category="PC",
    has_error=False,
    ged_input=_make_ged_input(
        text="ذهب الطالب، ثم عاد",
        tokens=[
            Token(index=0, form="ذهب", span=(0, 3), norm_span=(0, 3)),
            Token(index=1, form="الطالب", span=(4, 10), norm_span=(4, 10)),
            Token(index=2, form="،", span=(10, 11), norm_span=(10, 11)),
            Token(index=3, form="ثم", span=(12, 14), norm_span=(12, 14)),
            Token(index=4, form="عاد", span=(15, 18), norm_span=(15, 18)),
        ],
        morph_features=[
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="ذهب",
                    pos="VERB",
                    gender="masculine",
                    number="singular",
                    person="third",
                    tense="past",
                    voice="active",
                    diacritized="ذَهَبَ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="طالب",
                    pos="NOUN",
                    gender="masculine",
                    number="singular",
                    definiteness="definite",
                    case="nominative",
                    diacritized="الطَّالِبُ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=2,
                    lemma=None,
                    pos="PUNC",
                    diacritized=None,
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=3,
                    lemma="ثم",
                    pos="CONJ",
                    diacritized="ثُمَّ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=4,
                    lemma="عاد",
                    pos="VERB",
                    gender="masculine",
                    number="singular",
                    person="third",
                    tense="past",
                    voice="active",
                    diacritized="عَادَ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

_reg(
    "pc_space_before_comma_error",
    label="مسافة قبل الفاصلة : خطأ في التنسيق الإملائي",
    error_category="PC",
    has_error=True,
    ged_input=_make_ged_input(
        text="ذهب الطالب ، ثم عاد",
        tokens=[
            Token(index=0, form="ذهب", span=(0, 3), norm_span=(0, 3)),
            Token(index=1, form="الطالب", span=(4, 10), norm_span=(4, 10)),
            Token(index=2, form="،", span=(11, 12), norm_span=(11, 12)),
            Token(index=3, form="ثم", span=(13, 15), norm_span=(13, 15)),
            Token(index=4, form="عاد", span=(16, 19), norm_span=(16, 19)),
        ],
        morph_features=[
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="ذهب",
                    pos="VERB",
                    gender="masculine",
                    number="singular",
                    person="third",
                    tense="past",
                    voice="active",
                    diacritized="ذَهَبَ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="طالب",
                    pos="NOUN",
                    gender="masculine",
                    number="singular",
                    definiteness="definite",
                    case="nominative",
                    diacritized="الطَّالِبُ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=2,
                    lemma=None,
                    pos="PUNC",
                    diacritized=None,
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=3,
                    lemma="ثم",
                    pos="CONJ",
                    diacritized="ثُمَّ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=4,
                    lemma="عاد",
                    pos="VERB",
                    gender="masculine",
                    number="singular",
                    person="third",
                    tense="past",
                    voice="active",
                    diacritized="عَادَ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

# ===========================================================================
# MERGE (MG) : Incorrectly joined tokens
# ===========================================================================

_reg(
    "mg_incorrectly_merged_tokens_error",
    label="'عبدالله' مكتوبة كلمة واحدة : يجب أن تكون 'عبد الله' : خطأ في الدمج",
    error_category="MG",
    has_error=True,
    ged_input=_make_ged_input(
        text="عبدالله طالب",
        tokens=[
            Token(index=0, form="عبدالله", span=(0, 7), norm_span=(0, 7)),
            Token(index=1, form="طالب", span=(8, 12), norm_span=(8, 12)),
        ],
        morph_features=[
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="عبدالله",
                    pos="NOUN",
                    gender="masculine",
                    number="singular",
                    definiteness="indefinite",
                    case="nominative",
                    diacritized="عَبْدُاللَّهِ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="طالب",
                    pos="NOUN",
                    gender="masculine",
                    number="singular",
                    definiteness="indefinite",
                    case="nominative",
                    diacritized="طَالِبٌ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

_reg(
    "mg_correctly_split_tokens_correct",
    label="'عبد الله' مكتوبة كلمتين منفصلتين : صحيح",
    error_category="MG",
    has_error=False,
    ged_input=_make_ged_input(
        text="عبد الله طالب",
        tokens=[
            Token(index=0, form="عبد", span=(0, 3), norm_span=(0, 3)),
            Token(index=1, form="الله", span=(4, 8), norm_span=(4, 8)),
            Token(index=2, form="طالب", span=(9, 13), norm_span=(9, 13)),
        ],
        morph_features=[
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="عبد",
                    pos="NOUN",
                    gender="masculine",
                    number="singular",
                    definiteness="indefinite",
                    case="nominative",
                    diacritized="عَبْدُ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="الله",
                    pos="NOUN",
                    gender="masculine",
                    number="singular",
                    definiteness="definite",
                    case="genitive",
                    diacritized="اللَّهِ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=2,
                    lemma="طالب",
                    pos="NOUN",
                    gender="masculine",
                    number="singular",
                    definiteness="indefinite",
                    case="nominative",
                    diacritized="طَالِبٌ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

# ===========================================================================
# SPLIT (SP) : Incorrectly separated tokens
# ===========================================================================

_reg(
    "sp_incorrectly_split_tokens_error",
    label="'إنشاء الله' بكلمتين : الصواب 'إن شاء الله' : خطأ في الفصل",
    error_category="SP",
    has_error=True,
    ged_input=_make_ged_input(
        text="إنشاء الله",
        tokens=[
            Token(index=0, form="إنشاء", span=(0, 5), norm_span=(0, 5)),
            Token(index=1, form="الله", span=(6, 10), norm_span=(6, 10)),
        ],
        morph_features=[
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="إنشاء",
                    pos="NOUN",
                    gender="masculine",
                    number="singular",
                    definiteness="indefinite",
                    case="nominative",
                    diacritized="إِنْشَاءٌ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="الله",
                    pos="NOUN",
                    gender="masculine",
                    number="singular",
                    definiteness="definite",
                    case="genitive",
                    diacritized="اللَّهِ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)

_reg(
    "sp_correct_in_shaa_allah",
    label="'إن شاء الله' مكتوبة بثلاث كلمات منفصلة : صحيح",
    error_category="SP",
    has_error=False,
    ged_input=_make_ged_input(
        text="إن شاء الله",
        tokens=[
            Token(index=0, form="إن", span=(0, 2), norm_span=(0, 2)),
            Token(index=1, form="شاء", span=(3, 6), norm_span=(3, 6)),
            Token(index=2, form="الله", span=(7, 11), norm_span=(7, 11)),
        ],
        morph_features=[
            [
                MorphAnalysis(
                    token_index=0,
                    lemma="إن",
                    pos="PART",
                    diacritized="إِنْ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=1,
                    lemma="شاء",
                    pos="VERB",
                    gender="masculine",
                    number="singular",
                    person="third",
                    tense="past",
                    voice="active",
                    diacritized="شَاءَ",
                    is_disambiguated=True,
                )
            ],
            [
                MorphAnalysis(
                    token_index=2,
                    lemma="الله",
                    pos="NOUN",
                    gender="masculine",
                    number="singular",
                    definiteness="definite",
                    case="nominative",
                    diacritized="اللَّهُ",
                    is_disambiguated=True,
                )
            ],
        ],
    ),
)
