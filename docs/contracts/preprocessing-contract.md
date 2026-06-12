# Preprocessing Module Contract

**Author:** Akram Hany  
**Module:** Preprocessing (`src/services/preprocessing`)  
  
**Path in pipeline:** first — receives raw user input, feeds all downstream modules

---

## Input

| Field | Type | Description |
| --- | --- | --- |
| `text` | `str` | Raw Arabic text as typed by the user, unmodified |
| `cursor_offset` | `int|null` | Character offset of the cursor in `text`; `null` means end of input (default) |

> \[!NOTE\]  
> `cursor_offset` is reserved for mid-sentence editing support (DD-002) and is out of scope for the current phase. Implementations may ignore it and assume the cursor is always at the end.

---

## Output

| Field | Type | Description |
| --- | --- | --- |
| `text` | `str` | Original surface text, unmodified — all downstream spans reference this |
| `normalized_text` | `str` | Internally normalized text (Unicode, whitespace, Arabic character variants) |
| `tokens` | `list[Token]` | Completed tokens only, with character offsets on `text` |
| `morph_features` | `list[list[MorphAnalysis]]` | Per-token morphological candidates; outer list is indexed by token, inner list holds all candidates with the disambiguated one always first (`is_disambiguated: true`) |
| `current_fragment` | `str|null` | The incomplete word being typed; `null` when input ends with a delimiter |
| `mode` | `"NWP"|"WAC"` | Detected input mode (see Word Boundary Detection below) |

> \[!NOTE\]  
> `normalized_text` is an internal representation only. `Token.span` always references the original `text,` `Token.norm_span` references `normalized_text`. Downstream modules (GED, GEC, NWS) must use `span` , not `norm_span` , when reporting character offsets back to the user.

---

## Shared Data Structures

### `Token`

| Field | Type | Description |
| --- | --- | --- |
| `index` | `int` | Position of this token in the token list (0-based) |
| `form` | `str` | Surface form of the token taken from `normalized_text` (semantically equivalent to the original, `span` is provided for UI positioning purposes) |
| `span` | `tuple[int,int]` | Start and end character offsets on the original `text,` used by the UI to highlight characters the user actually typed |
| `norm_span` | `tuple[int,int]` | Start and end character offsets on `normalized_text`; may differ from `span` when NFKC expands a single codepoint into multiple characters |
| `affix_structure` | `str|null` | `+`\-joined clitic/stem breakdown derived from Farasa segmentation (ex. `CONJ+PREP+DET+STEM`), `null` for punctuation and non-Arabic tokens |

### `MorphAnalysis`

| Field | Type | Description |
| --- | --- | --- |
| `token_index` | `int` | Index of the corresponding `Token` |
| `lemma` | `str|null` | Base/root form of the token, `null` for punctuation and non-Arabic tokens |
| `pos` | `str` | Part-of-speech tag (see POS Tagset below) |
| `gender` | `str|null` | `masculine`, `feminine`, or `null` if not applicable |
| `number` | `str|null` | `singular`, `dual`, `plural`, or `null` if not applicable |
| `person` | `str|null` | `first`, `second`, `third`, or `null` if not applicable |
| `definiteness` | `str|null` | `definite`, `indefinite`, `null` if not applicable |
| `case` | `str|null` | `nominative`, `accusative`, `genitive`, or `null` if undetermined |
| `tense` | `str|null` | `past`, `present`, `imperative`, or `null` for non-verbs |
| `voice` | `str|null` | `active`, `passive`, or `null` for non-verbs |
| `mood` | `str|null` | `indicative`, `subjunctive`, `jussive`, or `null` for non-verbs |
| `diacritized` | `str|null` | The token form with full diacritics as resolved by disambiguation, `null` for punctuation and non-Arabic tokens |
| `is_disambiguated` | `bool` | `true` for the candidate selected by CAMeL’s disambiguator, `false` for all other candidates. The disambiguated candidate is always at index 0 of the inner list. |

> \[!NOTE\]  
> `MorphAnalysis` candidates are produced by CAMeL’s joint morphological analysis step. The disambiguator then selects one candidate as correct (`is_disambiguated: true`), which is always placed at index 0. The `diacritized` field on each candidate is CAMeL’s diacritization for that specific analysis (see DD-001).

> \[!NOTE\]  
> `affix_structure` lives on `Token`, not on `MorphAnalysis`, because it is a structural property of the token’s surface form derived from Farasa segmentation. It is fixed for a given token and does not vary across morphological analysis candidates.

---

## Pipeline Stages

text

Copy

```text
Raw text + cursor_offset        │        ▼[1] Normalization                         → normalized_text + norm_to_orig_map        │  Unicode NFKC + whitespace consolidation        │  norm_to_orig_map[i] = index of normalized_text[i] in original text        ▼[2] Word Boundary Detection               → completed_prefix, current_fragment, mode        │  Runs on normalized_text        │  Split into completed_prefix and current_fragment (see DD-002)        ▼[3] Segmentation — Farasa                 → list[Token]  (on completed_prefix only)        │  Farasa runs in interactive mode (JVM kept alive; fast repeated calls)        │  Farasa output (+‑split) → affix_structure per token        │  Sequential alignment → norm_span; norm_to_orig_map → span        │  Token.form = normalized_text[norm_span[0]:norm_span[1]]        ▼[4] Morphological Analysis + Disambiguation - CAMeL        │  Receives whole word forms (not Farasa sub-segments)        │  Joint morph analysis + diacritization in one pass (see DD-001)        ▼Output: tokens[], morph_features[], current_fragment, mode
```

---

## Word Boundary Detection

Determines whether the last token in the input is complete or still being typed (DD-002).

**Delimiter set** — a word is complete if followed by any of:

-   Whitespace: space, tab, newline
-   Arabic punctuation: `، ؟ ؛`
-   Shared punctuation: `. , ! ? ; : " ' ( ) [ ] { } - —`

**Detection logic:**

| Last character of input | `mode` | `current_fragment` |
| --- | --- | --- |
| Arabic letter or digit | `"WAC"` | last whitespace-delimited chunk extracted from the raw text before segmentation runs |
| Any delimiter | `"NWP"` | `null` |

> \[!NOTE\]  
> `current_fragment` receives only light normalization (alif variant canonicalization). It does **not** go through segmentation or morphological analysis. It is passed as-is to the NWS module for trie lookup.

> \[!IMPORTANT\]  
> GED and GEC must only operate on `tokens` (the completed prefix). The `current_fragment` must never be included in error detection.

---

## POS Tagset

| Tag | Description |
| --- | --- |
| `NOUN` | Noun |
| `VERB` | Verb |
| `ADJ` | Adjective |
| `ADV` | Adverb |
| `PREP` | Preposition |
| `CONJ` | Conjunction |
| `PRON` | Pronoun |
| `DET` | Determiner (`ال`) |
| `PART` | Particle |
| `PUNC` | Punctuation |
| `NUM` | Number |
| `INTJ` | Interjection |

---

## Affix Structure

`affix_structure` is a `+`\-joined string describing the components attached to the stem of a token, in left-to-right order. It is stored on `Token` (not `MorphAnalysis`) because it is a fixed structural property of the token’s surface form, computed once during segmentation from Farasa’s `+`\-split output. It is `null` for punctuation and non-Arabic tokens.

### Component Tags

| Tag | Description |
| --- | --- |
| `STEM` | The core word (always present in a valid affix structure) |
| `CONJ` | Conjunction clitic prefix (e.g. `و`, `ف`) |
| `PREP` | Preposition clitic prefix (e.g. `ب`, `ل`, `ك`) |
| `DET` | Definite article prefix (`ال`) |
| `PART` | Particle prefix (e.g. `ما`) |
| `PRON` | Pronoun suffix — possessive or object (e.g. `ه`, `ها`, `هم`) |

### Segmentation Algorithm

The segmenter peels known clitics from both ends of Farasa’s `+`\-split segments, working **inward**: known prefix clitics are consumed left-to-right first, then known suffix clitics right-to-left. Everything remaining in the middle is joined back together and tagged as `STEM`. This correctly handles Farasa’s over-segmentation of feminine stem endings (e.g. `مدرس+ة` → both parts unrecognised as clitics → joined as `STEM` = `مدرسة`).

**Known prefix clitics**

| Tag | Strings |
| --- | --- |
| `CONJ` | `و` `ف` |
| `PREP` | `ب` `ل` `ك` |
| `DET` | `ال` |
| `PART` | `ما` |

**Known suffix clitics**

| Tag | Strings |
| --- | --- |
| `PRON` | `ه` `ها` `هم` `هن` `ك` `كم` `نا` `ي` |

### Examples

| Surface form | `affix_structure` | Breakdown |
| --- | --- | --- |
| `ذهب` | `STEM` | stem only |
| `الطلاب` | `DET+STEM` | definite article + stem |
| `وبالمدرسة` | `CONJ+PREP+DET+STEM` | conjunction + preposition + det + stem |
| `كتبوه` | `STEM+PRON` | stem + object pronoun suffix |
| `وكتبها` | `CONJ+STEM+PRON` | conjunction + stem + possessive pronoun |
| `،` | `null` | punctuation — no affix structure |

---

## Example Output

Input: `"ذهب الطلاب، إلى المدرس"`

json

Copy

```json
{  "text": "ذهب الطلاب، إلى المدرس",  "normalized_text": "ذهب الطلاب، إلى المدرس",  "tokens": [    { "index": 0, "form": "ذهب",    "span": [0, 3],   "norm_span": [0, 3],   "affix_structure": "STEM" },    { "index": 1, "form": "الطلاب", "span": [4, 10],  "norm_span": [4, 10],  "affix_structure": "DET+STEM" },    { "index": 2, "form": "،",      "span": [10, 11], "norm_span": [10, 11], "affix_structure": null },    { "index": 3, "form": "إلى",    "span": [12, 15], "norm_span": [12, 15], "affix_structure": "STEM" }  ],  "morph_features": [    [      {        "token_index": 0, "lemma": "ذهب", "pos": "VERB",        "gender": "masculine", "number": "singular", "person": "third",        "definiteness": null, "case": null,        "tense": "past", "voice": "active", "mood": null,        "diacritized": "ذَهَبَ",        "is_disambiguated": true      },      {        "token_index": 0, "lemma": "ذَهَب", "pos": "NOUN",        "gender": "masculine", "number": "singular", "person": null,        "definiteness": "indefinite", "case": "nominative",        "tense": null, "voice": null, "mood": null,        "diacritized": "ذَهَبٌ",        "is_disambiguated": false      }    ],    [      {        "token_index": 1, "lemma": "طالب", "pos": "NOUN",        "gender": "masculine", "number": "plural", "person": null,        "definiteness": "definite", "case": "nominative",        "tense": null, "voice": null, "mood": null,        "diacritized": "الطُّلَابُ",        "is_disambiguated": true      }    ],    [      {        "token_index": 2, "lemma": null, "pos": "PUNC",        "gender": null, "number": null, "person": null,        "definiteness": null, "case": null,        "tense": null, "voice": null, "mood": null,        "diacritized": null,        "is_disambiguated": true      }    ],    [      {        "token_index": 3, "lemma": "إلى", "pos": "PREP",        "gender": null, "number": null, "person": null,        "definiteness": null, "case": null,        "tense": null, "voice": null, "mood": null,        "diacritized": "إِلَى",        "is_disambiguated": true      }    ]  ],  "current_fragment": "المدرس",  "mode": "WAC"}
```