# Ranker Module — Full Reference

**Module path:** `src/services/ranker`
**Pipeline position:** After GEC, before Explanation Generator
**Type:** Rule-based, deterministic, fully explainable

---

## 1. What the Ranker Does

The ranker receives error spans (from GED) and candidate corrections from multiple GEC submodules (Edit Tagger, Ontology, Dictionary), then **selects the single best correction per error span**. It eliminates no-op suggestions, scores every remaining candidate with 23 interpretable rules, and resolves overlapping edits so no token is corrected twice.

### High-level flow

```
GED error spans + GEC candidate edits
        │
        ▼
  ┌─────────────┐
  │ Aggregate    │  Group candidates by error span
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │ Filter      │  Drop no-op corrections (correction == original)
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │ Score       │  Apply 23 scoring rules per candidate
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │ Rank &      │  Sort by score, break ties, pick best per span
  │ Select      │
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │ Conflict     │  Greedy left-to-right; claim tokens,
  │ Resolution  │  skip candidates whose tokens are already claimed
  └──────┬──────┘
         ▼
  RankerOutput (ranked_edits + metadata)
```

---

## 2. Input / Output

### Input — `RankerInput`

| Field                | Type                | Source        | Description                        |
| -------------------- | ------------------- | ------------- | ---------------------------------- |
| `text`               | `str`               | Preprocessing | Original surface text              |
| `tokens`             | `list[Token]`       | Preprocessing | Token list (with `is_oov` flag)    |
| `errors_span`        | `list[ErrorSpan]`   | GED           | Detected error spans               |
| `errors_corrections` | `list[ModuleResult]`| GEC           | Candidate edits per GEC submodule  |

### Output — `RankerOutput`

| Field              | Type                | Description                                   |
| ------------------ | ------------------- | --------------------------------------------- |
| `text`             | `str`               | Echo of input text                            |
| `ranked_edits`     | `list[RankedEdit]`  | One selected edit per (non-conflicting) span  |
| `ranking_metadata` | `RankingMetadata`   | Aggregate stats                               |

#### `RankedEdit`

| Field             | Type             | Description                                     |
| ----------------- | ---------------- | ----------------------------------------------- |
| `error_id`        | `int`            | Index into the GED `errors_span` list           |
| `span`            | `tuple[int,int]` | Character offsets on the original text           |
| `token_refs`      | `list[int]`      | Token indices this edit touches                  |
| `correction`      | `str`            | The chosen correction string                     |
| `edit_operation`  | `str`            | `"keep"`, `"replace"`, `"insert"`, `"delete"`, `"merge"`, or `"split"` |
| `selected_module` | `str`            | Which GEC module won (`"ONTOLOGY"`, `"TAG"`, or `"DICTIONARY"`) |
| `final_score`     | `float`          | Aggregate score from all 23 rules                |

#### `RankingMetadata`

| Field                | Type            | Description                             |
| -------------------- | --------------- | --------------------------------------- |
| `global_confidence`  | `float`         | Mean final_score across all ranked edits |
| `module_utilization` | `dict[str,int]` | Count of edits selected per module       |

---

## 3. Candidate Types

The ranker scores three candidate edit types, one per GEC submodule:

### 3.1 `EditTaggerCandidateEdit` (TAG module)

ML-based sequence tagger output.

| Field              | Type                  | Notes                        |
| ------------------ | --------------------- | ---------------------------- |
| `span`             | `tuple[int,int]`      | Char offsets                 |
| `token_refs`       | `list[int]`           | Token indices                |
| `correction`       | `str`                 | Proposed text                |
| `edit_confidence`  | `float`               | Model confidence             |
| `edit_operation`   | `list[EditOperation]` | E.g. `[REPLACE]`, `[INSERT]` |

### 3.2 `OntologyCandidateEdit` (ONTOLOGY module)

Rule-based ontology/grammar corrections.

| Field              | Type         | Notes                                  |
| ------------------ | ------------ | -------------------------------------- |
| `span`             | `tuple[int,int]` | Char offsets                     |
| `token_refs`       | `list[int]`       | Token indices                    |
| `correction`       | `str`             | Proposed text                    |
| `edit_confidence`  | `float`           | Rule confidence                  |
| `group`            | `EditGroup`       | Atomic edit set metadata         |
| `is_independent`   | `bool`            | Whether the edit stands alone    |
| `group_explanation`| `str \| None`     | Group-level Arabic explanation   |

`EditGroup` has: `group_id: str`, `group_rank: int`, `explanation: str | None`.

### 3.3 `DictionaryCandidateEdit` (DICTIONARY module)

Dictionary/lexicon-based spelling corrections.

| Field              | Type         | Notes                              |
| ------------------ | ------------ | ---------------------------------- |
| `span`             | `tuple[int,int]` | Char offsets                 |
| `token_refs`       | `list[int]`       | Token indices                |
| `correction`       | `str`             | Proposed text                |
| `edit_confidence`  | `float`           | Lookup confidence            |
| `alternatives`     | `list[str]`       | Other valid spellings        |

---

## 4. Scoring — The 23 Rules

All weights are loaded from `config.yaml` and stored in `RankerConfig`. The score function is `score_candidate()` in `scoring.py`. Every rule is additive; penalties subtract. The final score is a simple sum.

### 4.1 Module Provenance Bonuses

These reward corrections from modules that are more likely to be right for certain error types.

| # | Weight            | Default | When Applied                                          | Rationale                                              |
|---|-------------------|---------|-------------------------------------------------------|--------------------------------------------------------|
| 1 | `W_ONTOLOGY`      | 0.25    | Candidate comes from the ONTOLOGY module              | Ontology has the highest trust — rule-based, deterministic |
| 2 | `W_TAG`           | 0.15    | Candidate comes from the TAG module                   | ML tagger is moderately trusted                        |
| 3 | `W_DICTIONARY`    | 0.10    | Candidate comes from the DICTIONARY module            | Dictionary is useful but narrower in scope            |

### 4.2 Ontology-Specific Bonuses

Only apply when the candidate is an `OntologyCandidateEdit`.

| # | Weight            | Default | When Applied                                                    | Rationale                                              |
|---|-------------------|---------|-----------------------------------------------------------------|--------------------------------------------------------|
| 4 | `W_INDEPENDENT`   | 0.05    | `candidate.is_independent == True`                              | Independent edits are self-contained, less likely to conflict with other edits |
| 5 | `W_GROUP_RANK`    | 0.10    | `candidate.group.group_rank > 0`, added as `W / group_rank`   | Higher-ranked groups within the ontology are more reliable. Rank 1 gets full weight, rank 2 gets half, etc. |

### 4.3 Dictionary-Specific Bonus

| # | Weight            | Default | When Applied                                                      | Rationale                                              |
|---|-------------------|---------|-------------------------------------------------------------------|--------------------------------------------------------|
| 6 | `W_FIRST_ALT`     | 0.05    | Candidate is from DICTIONARY and its correction matches the first alternative in `alternatives[]` | Being the top dictionary suggestion increases confidence |

### 4.4 Confidence Signals

| # | Weight            | Default | When Applied                                      | Rationale                                              |
|---|-------------------|---------|---------------------------------------------------|--------------------------------------------------------|
| 7 | `W_EDIT_CONF`    | 0.30    | Always; added as `W × edit_confidence`            | The candidate's own confidence is the strongest signal |
| 8 | `W_GED_CONF`     | 0.10    | Always; added as `W × error_span.confidence`     | If GED is very confident the span is an error, the correction is more likely needed |
| 9 | `W_LOW_CONF`      | 0.15    | When `edit_confidence < CONF_LOW_THRESHOLD` (0.30); **subtracted** | Penalizes very low-confidence candidates to weed out noise |

### 4.5 Provenance Tier Bonuses

GED assigns each error span a provenance tier indicating how it was detected.

| # | Weight            | Default | When Applied                                  | Rationale                                              |
|---|-------------------|---------|-----------------------------------------------|--------------------------------------------------------|
| 10| `W_TIER1`         | 0.15    | `provenance_tier == tier_1_rule_derived`      | Rule-derived detections are the most reliable          |
| 11| `W_TIER2`         | 0.08    | `provenance_tier == tier_2_rule_supported`    | Rule-supported detections are moderately reliable      |
| 12| `W_TIER3`         | 0.00    | `provenance_tier == tier_3_statistical`       | Purely statistical detections get no bonus (weight=0)  |

### 4.6 String Distance Penalties

These penalize corrections that are very different from the original, since GEC corrections in Arabic are typically small edits.

| # | Weight            | Default | When Applied                                              | Rationale                                              |
|---|-------------------|---------|-----------------------------------------------------------|--------------------------------------------------------|
| 13| `W_CHAR_DIST`     | 0.10    | Always; **subtracted** as `W × (levenshtein(orig, correction) / max_len)` | Large character edit distance suggests a less plausible single-edit correction |
| 14| `W_LENGTH_RATIO`   | 0.05    | Always; **subtracted** as `W × (|len_diff| / len(orig))`   | Big length changes are less likely for typical Arabic GEC fixes |

### 4.7 Empty Correction Penalty

| # | Weight            | Default | When Applied                                                                    | Rationale                                              |
|---|-------------------|---------|---------------------------------------------------------------------------------|--------------------------------------------------------|
| 15| `W_EMPTY`         | 0.50    | When correction is empty/whitespace AND the edit operation is **not** DELETE; **subtracted** | An empty correction that isn't an explicit delete is almost certainly wrong |

### 4.8 Error Category × Module Synergy Bonuses

These reward the alignment between the error type and the module's specialty.

| # | Weight            | Default | When Applied                                                  | Rationale                                              |
|---|-------------------|---------|---------------------------------------------------------------|--------------------------------------------------------|
| 16| `W_SPELL_DICT`    | 0.10    | Error category is ORTHOGRAPHY **and** module is DICTIONARY    | Dictionary is the best tool for spelling errors        |
| 17| `W_GRAM_ONT`      | 0.10    | Error category is SYNTAX or MORPHOLOGY **and** module is ONTOLOGY | Ontology rules are strongest for grammar errors  |
| 18| `W_EXPLAIN`       | 0.05    | `error_span.explanation_eligible == True` **and** module is ONTOLOGY | If the error is explainable and ontology is proposing, ontology can also produce the explanation |

### 4.9 Cross-Module Agreement

| # | Weight            | Default | When Applied                                                | Rationale                                              |
|---|-------------------|---------|-------------------------------------------------------------|--------------------------------------------------------|
| 19| `W_AGREEMENT`     | 0.20    | When ≥1 **other** module proposes the same correction text | Multiple independent modules agreeing is a very strong signal |

### 4.10 Error Span Properties

| # | Weight            | Default | When Applied                                   | Rationale                                              |
|---|-------------------|---------|-------------------------------------------------|--------------------------------------------------------|
| 20| `W_MULTI_SRC`     | 0.05    | `len(error_span.sources) > 1`                  | Error flagged by multiple GED sources is more likely real |
| 21| `W_OOV`           | 0.05    | Any token in `candidate.token_refs` has `is_oov == True` | Correcting an out-of-vocabulary token is especially valuable |

### 4.11 Identical-Edit Disqualification

| # | Rule                         | When Applied                               | Rationale                                              |
|---|------------------------------|--------------------------------------------|--------------------------------------------------------|
| — | `score = -infinity`          | `correction == original_text`              | A "correction" that doesn't change anything is not a correction at all — eliminated from ranking entirely |

### 4.12 Edit Operation Mismatch Penalty

Penalizes contradictions between the declared edit operation and the actual correction content.

| # | Weight            | Default | When Applied                                                               | Rationale                                              |
|---|-------------------|---------|----------------------------------------------------------------------------|--------------------------------------------------------|
| 22| `W_OP_MISMATCH`   | 0.20    | EditTagger says DELETE but correction is non-empty; **subtracted**         | A delete should produce empty text — mismatch is suspicious |
| 23| `W_OP_MISMATCH`   | 0.20    | EditTagger says INSERT but correction is empty; **subtracted**             | An insert should produce non-empty text — mismatch is suspicious |

> Note: rules 22 and 23 share the same `W_OP_MISMATCH` weight since they are both operation-consistency checks.

---

## 5. Aggregation & Matching — How Candidates Map to Error Spans

The `rank()` method in `RankerService` first groups candidates by error span:

1. Iterate over every `ModuleResult` from GEC.
2. For each candidate edit, find the first `ErrorSpan` it overlaps with.
3. Overlap is determined by `_matches()`:
   - **Span overlap**: the candidate's character span and the error span's character span intersect (i.e. they are not fully disjoint), **OR**
   - **Token overlap**: the candidate's `token_refs` and the error span's `token_refs` share at least one token index.

> If a candidate overlaps with multiple error spans, it is assigned to the **first** matching span (by enumeration order).

---

## 6. Filtering — No-op Elimination

Before scoring, any candidate whose `correction` equals the original text at the error span is removed. This prevents the scorer from wasting cycles on suggestions that don't actually change anything.

Additionally, within `score_candidate()`, if the correction matches the original text, the score is set to `float("-inf")`, which is a safety net that prevents such candidates from being selected even if they slip through the filter.

---

## 7. Ranking & Tie-Breaking

After scoring all candidates for an error span, they are sorted in descending order by:

```
key = (score, edit_confidence, module_priority, -correction_length)
```

| Component           | Direction | Rationale                                                      |
|---------------------|-----------|----------------------------------------------------------------|
| `score`             | ↓ highest | Better score wins                                              |
| `edit_confidence`   | ↓ highest | If scores are equal, prefer the more confident candidate      |
| `module_priority`   | ↓ highest | ONTOLOGY=3 > TAG=2 > DICTIONARY=1 — trust hierarchy            |
| `-correction_length`| ↑ shortest | If still tied, prefer shorter (more precise) corrections     |

---

## 8. Conflict Resolution — Token Claiming

Two edits that touch the same token would corrupt the text if both were applied. The ranker resolves this with a **greedy left-to-right** strategy:

1. Sort all error spans by their **start character offset** (leftmost first).
2. Maintain a `claimed_tokens: set[int]` of token indices already assigned to a selected edit.
3. For each span (in left-to-right order), iterate through its scored candidates (best first):
   - If the candidate's `token_refs` are **disjoint** from `claimed_tokens`, select it and add its tokens to the claimed set.
   - Otherwise, skip to the next candidate.
4. If no candidate for a span has unclaimed tokens, the span gets **no correction** in the output.

This ensures every token is corrected at most once, and earlier (leftmost) errors get priority.

---

## 9. Edit Operation Derivation

The output `edit_operation` field is derived from the candidate type:

- **EditTagger candidates**: the first element of `edit_operation[]` is mapped (`K→keep`, `R→replace`, `I→insert`, `D→delete`, `M→merge`, `S→split`).
- **All other candidates** (Ontology, Dictionary): defaults to `"replace"`.

---

## 10. Global Confidence & Module Utilization

After all edits are selected:

- **`global_confidence`** = mean of `final_score` across all selected edits. If no edits were selected, it is `0.0`. If there are no error spans at all (clean text), it is `1.0`.
- **`module_utilization`** = a dict counting how many edits each module won, e.g. `{"ONTOLOGY": 3, "DICTIONARY": 1}`.

---

## 11. Edge Cases

| Situation                               | Behavior                                                     |
| --------------------------------------- | ------------------------------------------------------------ |
| Empty input text                        | Return empty `ranked_edits`, `global_confidence = 0.0`       |
| No error spans detected                 | Return empty `ranked_edits`, `global_confidence = 1.0`       |
| GEC module returned `ModuleStatus.ERROR`| Its candidates are skipped during aggregation                |
| All candidates for a span are no-ops   | Span gets no correction (omitted from output)               |
| All candidates score `-inf`            | Span gets no correction                                      |
| Overlapping spans compete for tokens    | Leftmost span wins; losing span may get a lower-ranked candidate or none |
| Correction is empty but operation is DELETE | Not penalized (this is expected behavior)                   |

---

## 12. Configuration

All weights live in `src/services/ranker/config.yaml`:

```yaml
W_ONTOLOGY: 0.25
W_TAG: 0.15
W_DICTIONARY: 0.10
W_INDEPENDENT: 0.05
W_GROUP_RANK: 0.10
W_EDIT_CONF: 0.30
W_GED_CONF: 0.10
W_LOW_CONF: 0.15
CONF_LOW_THRESHOLD: 0.30
W_TIER1: 0.15
W_TIER2: 0.08
W_TIER3: 0.00
W_CHAR_DIST: 0.10
W_LENGTH_RATIO: 0.05
W_EMPTY: 0.50
W_SPELL_DICT: 0.10
W_GRAM_ONT: 0.10
W_EXPLAIN: 0.05
W_AGREEMENT: 0.20
W_MULTI_SRC: 0.05
W_OOV: 0.05
W_FIRST_ALT: 0.05
W_OP_MISMATCH: 0.20
```

Loading is done via `RankerConfig.from_yaml()` or the singleton `get_ranker_config()`. The `RankerConfig` class uses Pydantic, so all weights are validated as `float` and defaults are provided for every field.

---

## 13. File Map

| File                          | Purpose                                        |
| ----------------------------- | ---------------------------------------------- |
| `src/services/ranker/__init__.py` | Public API exports                         |
| `src/services/ranker/schemas.py`  | `RankerInput`, `RankerOutput`, `RankedEdit`, `RankingMetadata` |
| `src/services/ranker/config.py`   | `RankerConfig` (23 weights + YAML loader) |
| `src/services/ranker/config.yaml` | Default weight values                     |
| `src/services/ranker/scoring.py`  | `score_candidate()` function + `levenshtein()` |
| `src/services/ranker/ranker.py`   | `RankerService` class with `rank()` method |

---

## 14. Quick Example

Input text: `"ذهبوا الطلاب الى المدرسه"`

GED detects an error at span `(0, 5)` — the word `"ذهبوا"`.

Three GEC modules propose corrections:

| Module     | Correction | Confidence | Extra attributes             |
| ---------- | ---------- | ---------- | ---------------------------- |
| ONTOLOGY   | `"ذهب"`   | 0.90       | `is_independent=True`, `group_rank=1` |
| TAG        | `"ذهب"`   | 0.75       | `edit_operation=[REPLACE]`   |
| DICTIONARY | `"ذهبوا"` | 0.80       | `alternatives=["ذهبوا","ذهب"]` |

Scoring the ONTOLOGY candidate:

```
W_ONTOLOGY       = +0.25      (module provenance)
W_INDEPENDENT    = +0.05      (independent edit)
W_GROUP_RANK     = +0.10/1   = +0.10  (rank 1)
W_EDIT_CONF      = +0.30 × 0.90 = +0.27   (high confidence)
W_GED_CONF       = +0.10 × 0.85 = +0.085  (GED confidence)
W_TIER1          = +0.15      (rule-derived provenance)
W_CHAR_DIST      = -0.10 × (2/5) = -0.04  (levenshtein=2, max_len=5)
W_LENGTH_RATIO   = -0.05 × (2/5) = -0.02  (len delta=2, orig=5)
W_GRAM_ONT       = +0.10      (SYNTAX/MORPHOLOGY × ONTOLOGY)
W_AGREEMENT      = +0.20      (TAG also proposes "ذهب")
W_MULTI_SRC      = +0.05      (if multiple GED sources)
─────────────────────────────
Total ≈ +1.095
```

The DICTIONARY candidate proposes `"ذهبوا"` which equals the original text, so it gets `-inf` and is eliminated.

**ONTOLOGY wins** with the highest score, and the output `RankedEdit` records `selected_module="ONTOLOGY"`.

---

## 15. Design Principles

1. **No learned weights** — every coefficient is a named constant in YAML, tunable by hand.
2. **No external dependencies for scoring** — `levenshtein()` is implemented inline; no `python-Levenshtein` or `nltk` needed.
3. **Deterministic** — same input always produces same output.
4. **Explainable** — each score component can be traced to a specific rule and weight.
5. **Flat, not nested** — all 23 weights are top-level fields on `RankerConfig`; no nested sub-configs.
6. **Inline, not class-hierarchy** — all scoring rules live in one `score_candidate()` function rather than a rule class hierarchy, reducing indirection.
