# GEC Module Contract

**Author:**[Ahmed Hamed](https://github.com/AhmedHamed3699), [Somia Elshemy](https://github.com/somiaelshemy) <br>
**Module:** GEC (`src/services/gec`) <br>
**Path in pipeline:** after GED, before Ranker

---

## Input

| Field            | Type                  | Description                               |
| ---------------- | --------------------- | ----------------------------------------- |
| `text`           | `str`                 | Original surface text                     |
| `tokens`         | `list[Token]`         | Token boundaries aligned to original text |
| `morph_features` | `list[MorphAnalysis]` | Morphological analysis per token          |

## Output

A list of three objects, one for each GEC module:

- `module_name: str`
- `candidate_edits: list[CandidateEdit]`

---

## CandidateEdit

| Field               | Type             | Description                                     |
| ------------------- | ---------------- | ----------------------------------------------- | --------------------------------- |
| `error_id`          | `int`            | Index of the corresponding GED error            |
| `span`              | `tuple[int,int]` | Character offsets on original `text`            |
| `token_refs`        | `list[int]`      | Tokens affected                                 |
| `correction`        | `str`            | Proposed corrected surface form                 |
| `edit_operation`    | `str`            | `replace`, `insert`, `delete`, `merge`, `split` |
| `module_confidence` | `float`          | Score in `[0.0,1.0]`                            |
| `derivation_trace`  | `str             | null`                                           | Optional explanation/debug string |

---

## Example Output

Input sentence: `"ذهبوا الطلاب الى المدرسه"`

```json
{
  "module_name": "TAG",
  "candidates": [
    {
      "error_id": 0,
      "span": [0, 5],
      "token_refs": [0],
      "replacement": "ذهب",
      "edit_operation": "replace",
      "module_confidence": 0.94,
      "derivation_trace": "verb must be singular before plural subject"
    }
  ]
}
```
