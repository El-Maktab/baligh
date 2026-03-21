# GEC Module Contract

**Author:** [Ahmed Hamed](https://github.com/AhmedHamed3699), [Somia Elshemy](https://github.com/somiaelshemy)  
**Module:** GEC (`src/services/gec`)  
**Path in pipeline:** after GED, before Ranker

---

## Purpose

Defines the request/response contract for the GEC stage. The GEC stage returns outputs from three submodules:

- `TAG` - a sequence tagging model that identifies error spans and proposes edits with edit operations.
- `ONTOLOGY` - a rule-based module that applies linguistic and contextual rules to identify errors and propose edits, grouped into atomic edit sets.
- `DICTIONARY` - a dictionary-based module that identifies potential spelling and word choice errors and proposes corrections with alternatives.

Each submodule returns a status plus a list of candidate edits.

---

## Input Schema

### GECInput

| Field            | Type                  | Description                               |
| ---------------- | --------------------- | ----------------------------------------- |
| `text`           | `str`                 | Original surface text                     |
| `tokens`         | `list[Token]`         | Token boundaries aligned to original text |
| `morph_features` | `list[MorphAnalysis]` | Morphological analysis per token          |

---

## Output Schema

### GECOutput

`GECOutput` is a list of exactly three `ModuleResult` objects, one per module (`TAG`, `ONTOLOGY`, `DICTIONARY`).

### ModuleResult

| Field             | Type                  | Description                                          |
| ----------------- | --------------------- | ---------------------------------------------------- |
| `module_name`     | `ModuleName`          | Which GEC submodule produced this result             |
| `status`          | `ModuleStatus`        | Overall module decision                              |
| `candidate_edits` | `list[CandidateEdit]` | Proposed edits. May be empty when status is correct. |

### Enums

#### ModuleName

- `TAG`
- `ONTOLOGY`
- `DICTIONARY`

#### ModuleStatus

- `correct`
- `incorrect`
- `error`

---

## Candidate Edit Models

### Base: CandidateEdit

| Field             | Type              | Description                          |
| ----------------- | ----------------- | ------------------------------------ |
| `span`            | `tuple[int, int]` | Character offsets on original `text` |
| `token_refs`      | `list[int]`       | Indices of affected tokens           |
| `correction`      | `str`             | Proposed corrected surface form      |
| `edit_confidence` | `float`           | Confidence score in `[0.0, 1.0]`     |

### TAG: EditTaggerCandidateEdit

Inherits from `CandidateEdit` and adds:

| Field            | Type            | Description                          |
| ---------------- | --------------- | ------------------------------------ |
| `edit_operation` | `EditOperation` | Operation type for the proposed edit |

#### EditOperation

- `replace`
- `insert`
- `delete`
- `merge`
- `split`

### ONTOLOGY: OntologyCandidateEdit

Inherits from `CandidateEdit` and adds:

| Field            | Type        | Description                                               |
| ---------------- | ----------- | --------------------------------------------------------- |
| `group`          | `EditGroup` | Atomic edit set                                           |
| `is_independent` | `boolean`   | Whether this edit can be applied independent of the group |

#### EditGroup

| Field         | Type          | Description                 |
| ------------- | ------------- | --------------------------- |
| `group_id`    | `str`         | Edit group identifier       |
| `group_rank`  | `int`         | Edit group rank             |
| `explanation` | `str \| null` | Optional explanation string |

### DICTIONARY: DictionaryCandidateEdit

Inherits from `CandidateEdit` and adds:

| Field          | Type        | Description                                                |
| -------------- | ----------- | ---------------------------------------------------------- |
| `alternatives` | `list[str]` | Alternative corrections (ranked by confidence, best first) |

---

## Example

Input sentence: `"ذهبوا الطلاب الى المدرسه"`

```json
[
  {
    "module_name": "TAG",
    "status": "incorrect",
    "candidate_edits": [
      {
        "span": [0, 5],
        "token_refs": [0],
        "correction": "ذهب",
        "edit_confidence": 0.94,
        "edit_operation": "replace"
      }
    ]
  },
  {
    "module_name": "ONTOLOGY",
    "status": "incorrect",
    "candidate_edits": [
      {
        "span": [0, 5],
        "token_refs": [0],
        "correction": "ذهب",
        "edit_confidence": 0.98,
        "group": {
          "group_id": "G1",
          "group_rank": 1,
          "explanation": "إذا تقدم الفعل على الفاعل، يكون مفرداً"
        },
        "is_independent": false
      }
    ]
  },
  {
    "module_name": "DICTIONARY",
    "status": "incorrect",
    "candidate_edits": [
      {
        "span": [17, 24],
        "token_refs": [3],
        "correction": "المدرسة",
        "edit_confidence": 0.9,
        "alternatives": ["المدرسة", "المدرسي"]
      }
    ]
  }
]
```
