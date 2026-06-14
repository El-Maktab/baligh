# Grammatical Error Detection Rules

## Orthography (OT)

| Rule ID              | Subtype      | Implementation      | Tier                | Description (Arabic)                                                                        |
| -------------------- | ------------ | ------------------- | ------------------- | ------------------------------------------------------------------------------------------- |
| OT_ALIF_MAQSURA_PREP | alif_maqsura | YAML (Declarative)  | tier_1_rule_derived | وجوب كتابة الألف المقصورة (ى) في أواخر حروف الجر المحددة (على، إلى، حتى) بدلا من الياء (ي). |
| OT_TA_MARBUTA_NOUN   | ta_marbuta   | YAML (Declarative)  | tier_1_rule_derived | وجوب كتابة التاء المربوطة (ة) في أواخر الأسماء المؤنثة بدلا من الهاء (ه).                   |
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
