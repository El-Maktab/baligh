# NWS Module Contract

**Author:** Akram Hany  
**Module:** Next-Word Suggestion (`src/services/nws`)  
**Path in pipeline:** parallel fast path — receives preprocessing output directly, runs concurrently with GED/GEC

---

## Overview

The NWS module handles two prediction tasks, distinguished by the `mode` field set by preprocessing:

| Mode | Task | Input signal | Output |
| --- | --- | --- | --- |
| `"NWP"` | Next-Word Prediction | completed token context | Top-K predicted next words |
| `"WAC"` | Word Auto-Completion | `current_fragment` prefix | Top-K completions of the prefix |

A three-tier cache is checked before any model or trie lookup.

---

## Input

| Field | Type | Description |
| --- | --- | --- |
| `tokens` | `list[Token]` | Completed tokens from preprocessing, used as context window |
| `morph_features` | `list[list[MorphAnalysis]]` | Per-token morphological candidates (disambiguated candidate at index 0); used for context re-ranking |
| `current_fragment` | `str|null` | Incomplete word being typed; `null` in NWP mode |
| `mode` | `"NWP"|"WAC"` | Routing signal set by preprocessing |
| `top_k` | `int` | Maximum number of suggestions to return (caller-supplied; default 5) |

> \[!NOTE\]  
> `Token` and `MorphAnalysis` are defined in the Preprocessing contract. Only the disambiguated `MorphAnalysis` (index 0 of each inner list) is used for context-aware re-ranking.

---

## Output

| Field | Type | Description |
| --- | --- | --- |
| `mode` | `"NWP"|"WAC"` | Echoed from input |
| `suggestions` | `list[Suggestion]` | Ranked candidates, best suggestion at index 0; length ≤ `top_k` |

---

## Shared Data Structures

### `Suggestion`

| Field | Type | Description |
| --- | --- | --- |
| `rank` | `int` | 0-based position in the ranked list (0 = best) |
| `word` | `str` | The full suggested word. In NWP: the predicted next word. In WAC: the full word that completes `current_fragment` (not just the added suffix) |
| `score` | `float` | Confidence score in `[0.0, 1.0]`; higher is better |
| `source` | `str` | Which subsystem produced this suggestion (see Source Tags below) |

### Source Tags

| Tag | Description |
| --- | --- |
| `"idiom_cache"` | Matched from the static Arabic idioms cache |
| `"phrase_cache"` | Matched from the static famous phrases / common collocations cache |
| `"user_cache"` | Matched from the user-specific LRU pattern cache |
| `"model"` | Produced by the Next-Word Prediction core (NWP mode) |
| `"trie"` | Produced by the trie lookup + context-aware re-ranking (WAC mode) |

---

## Pipeline Stages

text

Copy

```text
tokens + morph_features + current_fragment + mode + top_k        │        ▼[1] Cache Key Construction        │  Normalize last-N token context (alif canonicalization)        │  WAC: append current_fragment prefix        ▼[2] Cache Lookup (all three tiers in order)        │  Tier 1: Idioms Cache (static)        │  Tier 2: Famous Phrases Cache (static)        │  Tier 3: User Patterns Cache (LRU, per-user)        │        ├── Cache HIT ──▶ return top_k from cache (source = tier tag)        │        └── Cache MISS                │                ▼[3] Mode Routing        ├── mode = "NWP" ──▶ [4a] Next-Word Prediction Core        │                          Language model scores candidates        │                          Context window: last-N tokens + morph features        │        └── mode = "WAC" ──▶ [4b] Trie Lookup                                   Retrieve all words with current_fragment prefix                                   │                                   ▼                              [4c] Context-Aware Re-ranking                                   Re-rank trie candidates using token context        │        ▼[5] User Cache Update        │  Write result to LRU cache (key → top_k suggestions)        ▼Output: suggestions[]
```

---

## Cache Layer

### Tier 1 — Idioms Cache (static)

A read-only lookup table of Arabic fixed expressions and idioms. A match fires when the normalized context suffix aligns with a known idiom prefix.

### Tier 2 — Famous Phrases Cache (static)

A read-only lookup table of common collocations and high-frequency phrase continuations (e.g. opening formulae, religious phrases).

### Tier 3 — User Patterns Cache (LRU, per-user)

A per-user LRU cache keyed on the normalized context. Populated automatically after each successful model or trie prediction.

> \[!NOTE\]  
> Cache tiers are checked in order (1 → 2 → 3). The first tier that returns a result short-circuits the lookup. If all tiers miss, the model or trie pipeline runs and the result is written back to Tier 3.

---

## Context Window

The context window fed to the prediction core and re-ranker is the last **N** completed tokens (default N = 5), using the surface `form` and the disambiguated `pos` and `lemma` from `morph_features[i][0]`.

> \[!NOTE\]  
> The exact value of N is an implementation concern and may be tuned per model. The contract only requires that the context is drawn from `tokens` and `morph_features` provided by preprocessing.

---

## WAC — Completion Semantics

In WAC mode, `word` in each `Suggestion` is the **complete word**, not the suffix added to `current_fragment`.

| `current_fragment` | `word` in suggestion | Not this |
| --- | --- | --- |
| `المدرس` | `المدرسة` | `ة` |
| `كت` | `كتاب` | `اب` |

The module does **not** filter suggestions that do not start with `current_fragment` — the trie lookup guarantees the prefix match.

---

## Example Output

Input context: `"ذهب الطلاب إلى"` + `current_fragment = "المدرس"`, `mode = "WAC"`, `top_k = 3`

json

Copy

```json
{  "mode": "WAC",  "suggestions": [    { "rank": 0, "word": "المدرسة",   "score": 0.87, "source": "trie"        },    { "rank": 1, "word": "المدرسين",  "score": 0.61, "source": "trie"        },    { "rank": 2, "word": "المدرسيات","score": 0.34, "source": "trie"        }  ]}
```

Input context: `"ذهب الطلاب إلى المدرسة "` + `current_fragment = null`, `mode = "NWP"`, `top_k = 3`

json

Copy

```json
{  "mode": "NWP",  "suggestions": [    { "rank": 0, "word": "في",    "score": 0.72, "source": "model" },    { "rank": 1, "word": "كل",   "score": 0.58, "source": "model" },    { "rank": 2, "word": "يوم",  "score": 0.41, "source": "user_cache" }  ]}
```