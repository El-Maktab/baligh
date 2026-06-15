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

## Semantics (SE)

| Rule ID | Subtype | Implementation | Tier | Description (Arabic) |
| ------- | ------- | -------------- | ---- | --------------------- |
| SE_DECADES_IYAT | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل في العقود الكتابة بصيغة «ـينيات» لا «ـينات»، مثل: الثلاثينيات. |
| SE_MOAKHARAN | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل تجنب «مؤخرا» بهذا المعنى، والأفصح: حديثًا أو قريبًا. |
| SE_MUTAAKID | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل استعمال «متحقق» أو «متيقن» بدل «متأكد». |
| SE_DHATA | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «ذواتا» بدل «ذاتا» في هذا الاستعمال. |
| SE_KHATIR | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل في هذا الاستعمال: شديد الخطر أو محفوف بالخطر بدل «خطير». |
| SE_KHAMMARA | lexical_usage | YAML (Declarative) | tier_1_rule_derived | «الخمارة» بائعة الخمر، ويستحسن للمكان: «مخمرة» أو «حانة». |
| SE_INDHAHALA | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الفعل الأفصح: «ذهل» لا «انذهل». |
| SE_BIAKMALIHI | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «كله» أو «جميعه» أو «برمته» بدل «بأكمله». |
| SE_TAHAMMAMA | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل استعمال «استحم» بدل «تحمم». |
| SE_TASHKILU | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يستحسن الاستغناء عن «تشكل» في هذا الاستعمال أو استبدالها بـ«هي». |
| SE_TASAMAMA | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الفعل المضعف هنا يدغم، والأفصح: «تصامّ» لا «تصامم». |
| SE_TATMIN | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الأفصح: «طمأنة» لا «تطمين». |
| SE_TA3KISU | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل في هذا السياق «تظهر» أو «تفضح» بدل «تعكس». |
| SE_JANOOBI | lexical_usage | YAML (Declarative) | tier_1_rule_derived | في الظرفية المكانية يفضل «جنوبَ» بدل «جنوبي». |
| SE_KHESISAN | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «خِصِّيصَى» أو «خاصًا» بدل «خصيصا». |
| SE_KHALOOQ | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل في الوصف هنا: «حسن الخلق» بدل «خلوق». |
| SE_RAGHMA | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «على الرغم» أو «بالرغم» أو «على» أو «مع» بدل «رغم». |
| SE_RAFAH | lexical_usage | YAML (Declarative) | tier_1_rule_derived | المستعمل هنا «رفات» لا «رفاة». |
| SE_SHAWYAN | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الأفصح في مصدر «شوى»: «شَيًّا» لا «شويا». |
| SE_ARAYA | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل في هذا المعنى «عريانـون» لا «عرايا». |
| SE_LIWAHDIHI | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الأفصح: «وحده» بدل «لوحده». |
| SE_MAHALAT | lexical_usage | YAML (Declarative) | tier_1_rule_derived | جمع «محل» في هذا الاستعمال هو «محالّ» لا «محلات». |
| SE_NAFOUKH | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الأفصح: «يافوخ» بدل «نافوخ». |
| SE_NASHET | lexical_usage | YAML (Declarative) | tier_1_rule_derived | في الوصف يفضل «نشيط» أو «ناشط» بدل «نشط». |
| SE_WALLATI | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يستحسن حذف الواو من «والتي» في هذا الربط. |
| SE_WALLADHI | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يستحسن حذف الواو من «والذي» في هذا الربط. |
| SE_ITTILA3 | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الأفصح: «اطّلاع» بدل «إطلاع». |
| SE_IDHTARADA | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الأفصح: «اطرّد» بدل «اضطرد». |
| SE_MUJBAA | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الأفصح: «مجبية» بدل «مجباة». |
| SE_MOUSOUD | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الأفصح: «موصَد» بدل «موصود». |
