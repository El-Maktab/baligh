# Ranker Module Contract

**Author:** [Somia Elshemy](https://github.com/somiaelshemy)  
**Module:** Ranker (`src/services/ranker`)  
**Path in pipeline:** after GEC, before Explanation Generator

---

## Input

| Field                | Type                    | Description                  |
| -------------------- | ----------------------- | ---------------------------- |
| `text`               | `str`                   | Original surface text        |
| `tokens`             | `list[Token]`           | Token list                   |
| `errors_span`        | `list[ErrorSpan]`       | GED output                   |
| `errors_corrections` | `list[GECModuleOutput]` | Outputs from all GEC modules |

---

## Output

An object with:

- `text: str`
- `ranked_edits: list[RankedEdit]`
- `ranking_metadata: RankingMetadata`

---

## RankedEdit

Represents the **selected correction per GED error span.**

| Field             | Type             | Description              |
| ----------------- | ---------------- | ------------------------ |
| `error_id`        | `int`            | Link to GED span         |
| `span`            | `tuple[int,int]` | Offsets on original text |
| `token_refs`      | `list[int]`      | Affected tokens          |
| `correction`      | `str`            | Chosen correction        |
| `edit_operation`  | `str`            | Operation type           |
| `selected_module` | `str`            | Selected module          |
| `final_score`     | `float`          | Ranking score            |

---

## RankingMetadata

| Field                | Type            | Description                         |
| -------------------- | --------------- | ----------------------------------- |
| `global_confidence`  | `float`         | Aggregate confidence across edits   |
| `module_utilization` | `dict[str,int]` | Number of selected edits per module |

---

## Example Output

```json
{
  "text": "ذهبوا الطلاب الى المدرسه",
  "ranked_edits": [
    {
      "error_id": 0,
      "span": [0, 5],
      "correction": "ذهب",
      "edit_operation": "replace",
      "selected_module": "rule_based_editor",
      "final_score": 0.91,
      "token_refs": [0]
    }
  ],
  "ranking_metadata": {
    "global_confidence": 0.88,
    "module_utilization": {
      "ONTOLOGY": 1,
      "TAGGER": 1
    }
  }
}
```

---
