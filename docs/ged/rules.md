# Grammatical Error Detection Rules

## Orthography (OT)

| Rule ID              | Subtype      | Implementation      | Tier                | Description (Arabic)                                                                        |
| -------------------- | ------------ | ------------------- | ------------------- | ------------------------------------------------------------------------------------------- |
| OT_ALIF_MAQSURA_PREP | alif_maqsura | YAML (Declarative)  | tier_1_rule_derived | وجوب كتابة الألف المقصورة (ى) في أواخر حروف الجر المحددة (على، إلى، حتى) بدلا من الياء (ي). |
| OT_TA_MARBUTA_NOUN   | ta_marbuta   | YAML (Declarative)  | tier_1_rule_derived | وجوب كتابة التاء المربوطة (ة) في أواخر الأسماء المؤنثة بدلا من الهاء (ه).                   |
| OT_HAMZA_ANNA        | hamza        | YAML (Declarative)  | tier_1_rule_derived | وجوب كتابة همزة القطع في «أن/إن» وصورهما المتصلة، مثل: أن، إنه، أنه، لا: ان، انه.           |
| OT_TA_MARBUTA_ADJ    | ta_marbuta   | YAML (Declarative)  | tier_1_rule_derived | وجوب كتابة التاء المربوطة (ة) في أواخر الصفات المؤنثة بدلا من الهاء (ه).                    |
| OT_TA_MARBUTA_NOUN_PROP | ta_marbuta | YAML (Declarative)  | tier_1_rule_derived | وجوب كتابة التاء المربوطة (ة) في أواخر الأعلام المؤنثة بدلا من الهاء (ه)، مثل: مكة، فاطمة. |
| OT_HAMZA_PREP        | hamza        | Python (Procedural) | tier_1_rule_derived | وجوب كتابة همزة القطع (أ/إ) في بداية حروف الجر والربط والأدوات بدلا من الألف المجردة (ا).   |

## Punctuation (PC)

| Rule ID              | Subtype | Implementation      | Tier                | Description (Arabic)                                                                  |
| -------------------- | ------- | ------------------- | ------------------- | ------------------------------------------------------------------------------------- |
| PC_SPACE_BEFORE_PUNC | spacing | Python (Procedural) | tier_1_rule_derived | وجوب اتصال علامات الترقيم (، ؟ ؛ . ! ؟) مباشرة بالكلمة التي تسبقها دون فاصل أو مسافة. |

## Syntax (SY)

| Rule ID                  | Subtype                  | Implementation      | Tier                | Description (Arabic)                                                                            |
| ------------------------ | ------------------------ | ------------------- | ------------------- | ----------------------------------------------------------------------------------------------- |
| SY_VERB_SUBJECT_VSO      | verb_subject_agreement   | Python (Procedural) | tier_1_rule_derived | وجوب إفراد الفعل وتجريده من علامات التثنية والجمع إذا تقدم على الفاعل الظاهر في الجملة الفعلية. |
| SY_NOUN_ADJ_DEFINITENESS | noun_adjective_agreement | Python (Procedural) | tier_1_rule_derived | وجوب مطابقة النعت للمنعوت في التعريف والتنكير.                                                  |
| SY_DEMONSTRATIVE_NOUN_GENDER | demonstrative_noun_gender | Python (Procedural) | tier_1_rule_derived | وجوب مطابقة اسم الإشارة للاسم الذي بعده في التذكير والتأنيث، مثل: هذا البطل، هذه السلامة.       |
| SY_RELATIVE_PRONOUN_GENDER | relative_pronoun_gender | Python (Procedural) | tier_1_rule_derived | وجوب مطابقة الاسم الموصول للاسم السابق له في التذكير والتأنيث، مثل: القول الذي، الوشاية التي.   |
| SY_PREP_DUAL_CASE | preposition_dual_case | Python (Procedural) | tier_1_rule_derived | وجوب جر الاسم المثنى بعد حرف الجر، مثل: في الكتابين لا في الكتابان.                            |
| SY_PREP_SOUND_MASC_PLURAL_CASE | preposition_sound_masc_plural_case | Python (Procedural) | tier_1_rule_derived | وجوب جر جمع المذكر السالم بعد حرف الجر، مثل: مع المسافرين لا مع المسافرون.                      |
