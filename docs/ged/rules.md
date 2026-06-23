# Grammatical Error Detection Rules

## Orthography (OT)

| Rule ID                 | Subtype      | Implementation      | Tier                | Description (Arabic)                                                                                          |
| ----------------------- | ------------ | ------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------- |
| OT_HAMZA_PREP           | hamza        | Python (Procedural) | tier_1_rule_derived | حروف الجر والربط وبعض الأدوات التي أصلها بهمزة قطع تكتب بالهمزة لا بالألف المجردة، مثل: إلى، أو، إذا، أن، إن. |
| OT_ALIF_MAQSURA_ALA     | alif_maqsura | YAML (Declarative)  | tier_1_rule_derived | الصواب «على» لا «علي».                                                                                        |
| OT_ALIF_MAQSURA_HATTA   | alif_maqsura | YAML (Declarative)  | tier_1_rule_derived | الصواب «حتى» لا «حتي».                                                                                        |
| OT_TANWIN_NASB_ON_ALIF  | tanwin       | YAML (Declarative)  | tier_1_rule_derived | تنوين النصب يكتب على الحرف الذي قبل الألف لا على الألف نفسها.                                                 |
| OT_IDGHAM_AN_MA         | idgham       | YAML (Declarative)  | tier_1_rule_derived | الأفصح إدغام «عن ما» في «عمّا» عندما تليها جملة فعلية.                                                        |
| OT_IDGHAM_MIN_MA        | idgham       | YAML (Declarative)  | tier_1_rule_derived | الأفصح إدغام «من ما» في «ممّا» عندما تليها جملة فعلية.                                                        |
| OT_TA_MARBUTA_NOUN      | ta_marbuta   | YAML (Declarative)  | tier_1_rule_derived | وجوب كتابة التاء المربوطة (ة) في أواخر الأسماء المؤنثة بدلا من الهاء (ه).                                     |
| OT_TA_MARBUTA_ADJ       | ta_marbuta   | YAML (Declarative)  | tier_1_rule_derived | وجوب كتابة التاء المربوطة (ة) في أواخر الصفات المؤنثة بدلا من الهاء (ه).                                      |
| OT_TA_MARBUTA_NOUN_PROP | ta_marbuta   | YAML (Declarative)  | tier_1_rule_derived | وجوب كتابة التاء المربوطة (ة) في أواخر الأعلام المؤنثة بدلا من الهاء (ه)، مثل: مكة، فاطمة.                    |

## Punctuation (PC)

| Rule ID              | Subtype | Implementation      | Tier                | Description (Arabic)                                                                  |
| -------------------- | ------- | ------------------- | ------------------- | ------------------------------------------------------------------------------------- |
| PC_SPACE_BEFORE_PUNC | spacing | Python (Procedural) | tier_1_rule_derived | وجوب اتصال علامات الترقيم (، ؟ ؛ . ! ؟) مباشرة بالكلمة التي تسبقها دون فاصل أو مسافة. |
| PC_LATIN_COMMA_ARABIC | variant | Python (Procedural) | tier_1_rule_derived | في السياق العربي تستعمل الفاصلة العربية «،» لا الفاصلة اللاتينية «,». |
| PC_LATIN_QUESTION_ARABIC | variant | Python (Procedural) | tier_1_rule_derived | في السياق العربي تستعمل علامة الاستفهام العربية «؟» لا العلامة اللاتينية «?». |
| PC_LATIN_SEMICOLON_ARABIC | variant | Python (Procedural) | tier_1_rule_derived | في السياق العربي تستعمل الفاصلة المنقوطة العربية «؛» لا «;». |

## Syntax (SY)

| Rule ID                            | Subtype                            | Implementation      | Tier                | Description (Arabic)                                                                            |
| ---------------------------------- | ---------------------------------- | ------------------- | ------------------- | ----------------------------------------------------------------------------------------------- |
| SY_DEM_HADHANI_FEM                 | demonstrative_dual_gender          | YAML (Declarative)  | tier_1_rule_derived | الصواب «هاتان» مع الاسم المثنى المؤنث لا «هذان».                                                |
| SY_DEM_HATANI_MASC                 | demonstrative_dual_gender          | YAML (Declarative)  | tier_1_rule_derived | الصواب «هذان» مع الاسم المثنى المذكر لا «هاتان».                                                |
| SY_DEM_HADHAYNI_FEM                | demonstrative_dual_gender          | YAML (Declarative)  | tier_1_rule_derived | الصواب «هاتين» مع الاسم المثنى المؤنث لا «هذين».                                                |
| SY_DEM_HATAYNI_MASC                | demonstrative_dual_gender          | YAML (Declarative)  | tier_1_rule_derived | الصواب «هذين» مع الاسم المثنى المذكر لا «هاتين».                                                |
| SY_DEM_HADHANI_CASE_OBLIQUE_NOUN   | demonstrative_dual_case            | YAML (Declarative)  | tier_1_rule_derived | إذا جاء بعد «هذان» اسم مثنى مذكر غير مرفوع فهناك خلل في المطابقة الإعرابية.                     |
| SY_DEM_HADHAYNI_CASE_NOM_NOUN      | demonstrative_dual_case            | YAML (Declarative)  | tier_1_rule_derived | إذا جاء بعد «هذين» اسم مثنى مذكر مرفوع فهناك خلل في المطابقة الإعرابية.                         |
| SY_DEM_PREP_HADHAYNI_CASE_NOM_NOUN | demonstrative_dual_case            | YAML (Declarative)  | tier_1_rule_derived | بعد حرف الجر يكون الاسم بعد «هذين» مجرورًا لا مرفوعًا.                                          |
| SY_DEM_HATANI_CASE_OBLIQUE_NOUN    | demonstrative_dual_case            | YAML (Declarative)  | tier_1_rule_derived | إذا جاء بعد «هاتان» اسم مثنى مؤنث غير مرفوع فهناك خلل في المطابقة الإعرابية.                    |
| SY_DEM_HATAYNI_CASE_NOM_NOUN       | demonstrative_dual_case            | YAML (Declarative)  | tier_1_rule_derived | إذا جاء بعد «هاتين» اسم مثنى مؤنث مرفوع فهناك خلل في المطابقة الإعرابية.                        |
| SY_DEM_PREP_HATAYNI_CASE_NOM_NOUN  | demonstrative_dual_case            | YAML (Declarative)  | tier_1_rule_derived | بعد حرف الجر يكون الاسم بعد «هاتين» مجرورًا لا مرفوعًا.                                         |
| SY_LAM_JUSSIVE                     | jussive_operator                   | YAML (Declarative)  | tier_1_rule_derived | الفعل المضارع بعد «لم» يجب أن يكون مجزومًا.                                                     |
| SY_LAMMA_JUSSIVE                   | jussive_operator                   | YAML (Declarative)  | tier_1_rule_derived | الفعل المضارع بعد «لما» يجب أن يكون مجزومًا.                                                    |
| SY_LA_NAHIYA_JUSSIVE               | jussive_operator                   | YAML (Declarative)  | tier_1_rule_derived | الفعل المضارع بعد «لا» الناهية يجب أن يكون مجزومًا.                                             |
| SY_LA_NAFIYA_NOT_JUSSIVE           | jussive_operator                   | YAML (Declarative)  | tier_1_rule_derived | «لا» النافية لا تجزم الفعل المضارع.                                                             |
| SY_INNA_SISTERS_DUAL_ACCUSATIVE    | inna_sisters_case                  | YAML (Declarative)  | tier_1_rule_derived | أخوات إن تنصب الاسم، والمثنى بعدها يكون منصوبًا بالياء لا مرفوعًا.                              |
| SY_VERB_SUBJECT_VSO                | verb_subject_agreement             | Python (Procedural) | tier_1_rule_derived | وجوب إفراد الفعل وتجريده من علامات التثنية والجمع إذا تقدم على الفاعل الظاهر في الجملة الفعلية. |
| SY_NOUN_ADJ_DEFINITENESS           | noun_adjective_agreement           | Python (Procedural) | tier_1_rule_derived | وجوب مطابقة النعت للمنعوت في التعريف والتنكير.                                                  |
| SY_DEMONSTRATIVE_NOUN_GENDER       | demonstrative_noun_gender          | Python (Procedural) | tier_1_rule_derived | وجوب مطابقة اسم الإشارة للاسم الذي بعده في التذكير والتأنيث، مثل: هذا البطل، هذه السلامة.       |
| SY_RELATIVE_PRONOUN_GENDER         | relative_pronoun_gender            | Python (Procedural) | tier_1_rule_derived | وجوب مطابقة الاسم الموصول للاسم السابق له في التذكير والتأنيث، مثل: القول الذي، الوشاية التي.   |
| SY_PREP_DUAL_CASE                  | preposition_dual_case              | Python (Procedural) | tier_1_rule_derived | وجوب جر الاسم المثنى بعد حرف الجر، مثل: في الكتابين لا في الكتابان.                             |
| SY_PREP_SOUND_MASC_PLURAL_CASE     | preposition_sound_masc_plural_case | Python (Procedural) | tier_1_rule_derived | وجوب جر جمع المذكر السالم بعد حرف الجر، مثل: مع المسافرين لا مع المسافرون.                      |

## Semantics (SE)

| Rule ID         | Subtype       | Implementation     | Tier                | Description (Arabic)                                                   |
| --------------- | ------------- | ------------------ | ------------------- | ---------------------------------------------------------------------- |
| SE_DECADES_IYAT | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل في العقود الكتابة بصيغة «ـينيات» لا «ـينات»، مثل: الثلاثينيات.    |
| SE_MOAKHARAN    | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل تجنب «مؤخرا» بهذا المعنى، والأفصح: حديثًا أو قريبًا.              |
| SE_MUTAAKID     | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل استعمال «متحقق» أو «متيقن» بدل «متأكد».                           |
| SE_DHATA        | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «ذواتا» بدل «ذاتا» في هذا الاستعمال.                              |
| SE_KHATIR       | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل في هذا الاستعمال: شديد الخطر أو محفوف بالخطر بدل «خطير».          |
| SE_KHAMMARA     | lexical_usage | YAML (Declarative) | tier_1_rule_derived | «الخمارة» بائعة الخمر، ويستحسن للمكان: «مخمرة» أو «حانة».              |
| SE_INDHAHALA    | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الفعل الأفصح: «ذهل» لا «انذهل».                                        |
| SE_BIAKMALIHI   | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «كله» أو «جميعه» أو «برمته» بدل «بأكمله».                         |
| SE_TAHAMMAMA    | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل استعمال «استحم» بدل «تحمم».                                       |
| SE_TASHKILU     | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يستحسن الاستغناء عن «تشكل» في هذا الاستعمال أو استبدالها بـ«هي».       |
| SE_TASAMAMA     | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الفعل المضعف هنا يدغم، والأفصح: «تصامّ» لا «تصامم».                    |
| SE_TATMIN       | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الأفصح: «طمأنة» لا «تطمين».                                            |
| SE_TA3KISU      | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل في هذا السياق «تظهر» أو «تفضح» بدل «تعكس».                        |
| SE_JANOOBI      | lexical_usage | YAML (Declarative) | tier_1_rule_derived | في الظرفية المكانية يفضل «جنوبَ» بدل «جنوبي».                          |
| SE_KHESISAN     | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «خِصِّيصَى» أو «خاصًا» بدل «خصيصا».                               |
| SE_KHALOOQ      | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل في الوصف هنا: «حسن الخلق» بدل «خلوق».                             |
| SE_RAGHMA       | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «على الرغم» أو «بالرغم» أو «على» أو «مع» بدل «رغم».               |
| SE_RAFAH        | lexical_usage | YAML (Declarative) | tier_1_rule_derived | المستعمل هنا «رفات» لا «رفاة».                                         |
| SE_SHAWYAN      | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الأفصح في مصدر «شوى»: «شَيًّا» لا «شويا».                              |
| SE_ARAYA        | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل في هذا المعنى «عريانـون» لا «عرايا».                              |
| SE_LIWAHDIHI    | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الأفصح: «وحده» بدل «لوحده».                                            |
| SE_MAHALAT      | lexical_usage | YAML (Declarative) | tier_1_rule_derived | جمع «محل» في هذا الاستعمال هو «محالّ» لا «محلات».                      |
| SE_NAFOUKH      | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الأفصح: «يافوخ» بدل «نافوخ».                                           |
| SE_NASHET       | lexical_usage | YAML (Declarative) | tier_1_rule_derived | في الوصف يفضل «نشيط» أو «ناشط» بدل «نشط».                              |
| SE_WALLATI      | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يستحسن حذف الواو من «والتي» في هذا الربط.                              |
| SE_WALLADHI     | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يستحسن حذف الواو من «والذي» في هذا الربط.                              |
| SE_ITTILA3      | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الأفصح: «اطّلاع» بدل «إطلاع».                                          |
| SE_IDHTARADA    | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الأفصح: «اطرّد» بدل «اضطرد».                                           |
| SE_MUJBAA       | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الأفصح: «مجبية» بدل «مجباة».                                           |
| SE_MOUSOUD      | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الأفصح: «موصَد» بدل «موصود».                                           |
| SE_MUASHIRAT    | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يستحسن في هذا المعنى: إشارات أو علامات أو شواهد أو دلائل بدل «مؤشرات». |
| SE_MISHWAR      | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يستحسن تجنب «مشوار» بهذا المعنى، والأفصح: طريق أو مسار أو نزهة.        |
| SE_MACHINE      | lexical_usage | YAML (Declarative) | tier_1_rule_derived | الأفصح: «مكنة» بدل «ماكينة».                                           |
| SE_IMKANIYAT    | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «إمكانات» بدل «إمكانيات».                                         |
| SE_TAWAJUD      | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل في هذا الاستعمال «وجد» بدل «تواجد».                               |
| SE_MUSBAQAN     | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «مقدمًا» أو «سلفًا» أو «قبلًا» بدل «مسبقا».                       |
| SE_WABITTALI    | lexical_usage | YAML (Declarative) | tier_1_rule_derived | «وبالتالي» تعبير ركيك في هذا السياق، ويستحسن استبداله ببدائل أفصح.     |
| SE_BIMATHABATI  | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «بمنزلة» أو «تقوم مقام» بدل «بمثابة».                             |
| SE_ISTIBYAN     | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «استبانة» بدل «استبيان».                                          |
| SE_AKHISSAI     | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «اختصاصي» بدل «أخصائي».                                           |
| SE_TOQOS        | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «شعائر» بدل «طقوس» في هذا الاستعمال.                              |
| SE_BIHASABI     | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يستحسن تجنب «بحسب» في هذا الاستعمال واستبدالها ببدائل أفصح.            |
| SE_LISALIHIKA   | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «لمصلحتك» بدل «لصالحك».                                           |
| SE_LISALIHI     | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «لمصلحة» بدل «لصالح».                                             |
| SE_I3TABAR      | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل في هذا الاستعمال «عدّ» بدل «اعتبر».                               |
| SE_BURHA        | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «هنيهة» بدل «برهة» في هذا السياق.                                 |
| SE_AAWINA       | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «أوان» بدل «آونة».                                                |
| SE_BAWASIL      | lexical_usage | YAML (Declarative) | tier_1_rule_derived | في هذا الاستعمال يفضل «بسلاء» أو «باسلون» بدل «بواسل».                 |
| SE_MUSTAHTIR    | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «مستهين» أو «مستخفّ» بدل «مستهتر» في هذا الاستعمال.               |
| SE_SUWAH        | lexical_usage | YAML (Declarative) | tier_1_rule_derived | يفضل «سياح» بدل «سواح».                                                |
| SE_KAKULL       | lexical_usage | YAML (Declarative) | tier_1_rule_derived | «ككل» ترجمة ركيكة، ويستحسن «كليًا».                                    |
