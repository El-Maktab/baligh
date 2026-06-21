# GED Evaluation

The evaluator measures the rule-based, lexicon, and sequence-labeling detectors
individually and after fusion.

## Corpora

- QALB14
- QALB15 L1
- QALB15 L2
- ZAEBUC

## Running

Run all datasets with:

```bash
make ged-evaluate
```

For a quick smoke run or a selected corpus:

```bash
uv run python -m src.services.ged.evaluation --dataset qalb14 --limit 5
```

The command logs GED tables and writes the full report to
`artifacts/ged/evaluation/report.json`. Use `--output` to select another path.

## Evaluation policy

Token-only corpora do not preserve the whitespace needed to evaluate the
`spacing` punctuation rule, so that rule is filtered only by the evaluator;
production behavior remains enabled. Semantic predictions remain visible in
the category diagnostics but do not affect primary scores because these
corpora contain no `SE` annotations.
