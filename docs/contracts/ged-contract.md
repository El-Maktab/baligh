# GED Module Contract

**Author:** [Amir Kedis](https://github.com/amir-kedis) <br>
**Module:** Grammatical Error Detection (`src/services/ged`) <br>
**Path in pipeline:** after Preprocessing, before GEC

---

## Input

| Field             | Type                  | Description                                                       |
| ----------------- | --------------------- | ----------------------------------------------------------------- |
| `text`            | `str`                 | Original surface text, unmodified                                 |
| `normalized_text` | `str`                 | Internally normalized text (Unicode, whitespace, Arabic variants) |
| `tokens`          | `list[Token]`         | Token boundaries with character offsets on original text          |
| `morph_features`  | `list[MorphAnalysis]` | Per-token morphological features **\***                           |

> [!NOTE]
> `normalized_text` is an internal representation only. GED must map all output spans back to offsets on `text`.<br>
> `MorphAnalysis` includes POS, lemma, gender, number, person, definiteness, case candidates, affix structure, etc.<br>
> `Token` and `MorphAnalysis` are shared data structures that should be defined in a separate contract file.

---

## Output

An object with:

- `text: str`
- `errors: list[ErrorSpan]`

Each `ErrorSpan` has:

| Field                  | Type              | Description                                                                              |
| ---------------------- | ----------------- | ---------------------------------------------------------------------------------------- |
| `span`                 | `tuple[int, int]` | Start and end character offsets on the original `text`                                   |
| `token_refs`           | `list[int]`       | Indices of affected tokens                                                               |
| `category`             | `str`             | Top-level error category (see taxonomy below)                                            |
| `subtype`              | `str`             | Specific error subtype (e.g. `hamza`, `ta_marbuta`, `verb_subject_agreement`)            |
| `confidence`           | `float`           | Score in `[0.0, 1.0]`                                                                    |
| `sources`              | `list[str]`       | Which subsystems flagged this span (`rule_based`, `lexicon_matcher`, `sequence_labeler`) |
| `provenance_tier`      | `str`             | `tier_1_rule_derived`, `tier_2_rule_supported`, or `tier_3_statistical`                  |
| `explanation_eligible` | `bool`            | Whether a human-readable explanation can be attached                                     |
| `explanation_text`     | `str \| null`     | Arabic explanation string for `tier_1` and `tier_2` spans; `null` for `tier_3`           |

---

## Error Taxonomy

| Category                   | Code | Notes                                      |
| -------------------------- | ---- | ------------------------------------------ |
| Orthography                | `OT` | Hamza, ta marbuta, alif variants, spelling |
| Morphology                 | `MO` | Inflection, verb form, number, gender      |
| Syntax                     | `SY` | Agreement, case-governed form              |
| Semantics / Lexical Choice | `SE` | Choice of word\*                           |
| Punctuation                | `PC` | Missing, extra, or wrong punctuation       |
| Merge                      | `MG` | Incorrectly joined tokens                  |
| Split                      | `SP` | Incorrectly separated tokens               |

> [!NOTE]
> The `SE` category has limited scope and is treated as an optional advanced feature.

---

## Fusion Policy

Detection is merged from three subsystems in priority order:

1. Rule-based detector (highest precision, `tier_1`)
2. Lexicon and pattern matcher (`tier_1` / `tier_2`)
3. Sequence labeler (`tier_2` / `tier_3`)

> [!NOTE]
> When two subsystems disagree on the same span, the higher-confidence source wins.

---

## Example Output

Input sentence: `"ذهبوا الطلاب الى المدرسه"`

```json
{
  "text": "ذهبوا الطلاب الى المدرسه",
  "errors": [
    {
      "span": [0, 5],
      "token_refs": [0],
      "category": "SY",
      "subtype": "verb_subject_agreement",
      "confidence": 0.93,
      "sources": ["sequence_labeler", "rule_based"],
      "provenance_tier": "tier_2_rule_supported",
      "explanation_eligible": true,
      "explanation_text": "إذا تقدم الفعل على الفاعل، يكون مفرداً"
    },
    {
      "span": [13, 16],
      "token_refs": [2],
      "category": "OT",
      "subtype": "hamza",
      "confidence": 0.99,
      "sources": ["rule_based"],
      "provenance_tier": "tier_1_rule_derived",
      "explanation_eligible": true,
      "explanation_text": "حرف الجر إلى يُكتب بهمزة قطع"
    },
    {
      "span": [17, 24],
      "token_refs": [3],
      "category": "OT",
      "subtype": "ta_marbuta",
      "confidence": 0.99,
      "sources": ["rule_based"],
      "provenance_tier": "tier_1_rule_derived",
      "explanation_eligible": true,
      "explanation_text": "كلمة المدرسة تنتهي بتاء مربوطة لا بهاء"
    }
  ]
}
```
