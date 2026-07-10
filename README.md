<!-- markdownlint-disable MD033 -->
<!-- markdownlint-disable MD034 -->
<!-- markdownlint-disable MD041 -->

<p align="center">
  <img src="./assets/logo.png" width="210" alt="Baligh Logo" />
</p>

<p align="center">
  Arabic writing assistance for Modern Standard Arabic,<br>
  built around explainable correction, linguistic evidence, and fast suggestions.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-active%20development-C7502E?style=flat-square" alt="Status: active development">
  <img src="https://img.shields.io/badge/license-proprietary-1B1B1B?style=flat-square" alt="License: proprietary">
</p>

https://github.com/user-attachments/assets/f5f6ddc8-5b6f-40d5-a7a4-1a9052c67ab8

---

## <img align="center" height="50" src="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExZTJ1YXdzbWx6Zm4wOXlsZ3d3cW1mMmZwdHcza2M5a2xxaWZpeGVkYyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/AqUFBbklXep9eliq0L/giphy.gif" alt="Arabic typography animation"> What Is Baligh?

**Baligh (بليغ)** is a graduation-project Arabic NLP system for helping people write correct, fluent Modern Standard Arabic. It combines grammatical error detection, grammatical error correction, and next-word suggestion in one interactive writing pipeline.

The project is intentionally not a black-box rewriting tool. Every surfaced correction is designed to carry evidence: a rule, a linguistic category, a source module, or a confidence trail that explains why the suggestion exists.


---

## <img align="center" height="50" src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExY2Fva3k4MTk5YnVkdWFoeDZtdm05Y3Y5ZnFwb3l5ZXFveWhnZWNhbiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/vkYqm6lzPydFimucNz/giphy.gif" alt="Arabic calligraphy animation"> The Pipeline

<p align="center">
  <img src="./assets/high-level-architecture.png" alt="Baligh high-level architecture" width="100%">
</p>

Baligh separates lightweight interaction from deeper analysis. The fast path handles word completion and next-word suggestion while the user is typing. The slower path runs grammatical detection, correction, ranking, and explanation once enough context is available.

---

## <img align="center" height="50" src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExenJvM3Q4MW00a3A0YTA5dHNrYzM2MjFkb3UxYXVoajN4aDY1Nzd1NSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/vozFa8CFpLmNKeR3EW/giphy.gif" alt="Arabic typography animation"> Core Features

### Grammatical Error Detection

The GED layer finds spans that may contain orthographic, morphological, syntactic, punctuation, merge, or split errors. It fuses rule-based detectors, lexicon and pattern matchers, and learned sequence-labeling signals into a single ranked error list.

<p align="center">
  <img src="./assets/ged-architecture.png" alt="GED module architecture" width="100%">
</p>

### Grammatical Error Correction

The GEC layer proposes edits using multiple correction sources: ontology-backed grammatical constraints, dictionary-based spelling and lexical candidates, and edit-tagger models. A ranker then chooses the strongest candidates using confidence, provenance, and edit quality.

<p align="center">
  <img src="./assets/gec-architecture.png" alt="GEC module architecture" width="100%">
</p>

### Next Word Suggestion

The NWS layer supports both next-word prediction and word auto-completion. It uses cached phrases, trie lookup, language-model scoring, and context-aware re-ranking so suggestions stay responsive during live typing.

<p align="center">
  <img src="./assets/nws-architecture.png" alt="NWS module architecture" width="100%">
</p>

### Explanation First

Baligh tracks provenance across the pipeline. A correction can be rule-derived, rule-supported, or statistical, and the UI/API contract keeps that distinction visible instead of presenting every suggestion with the same certainty.

---


## <img align="center" height="50" src="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExMHc5bTZtNGU3NGh3ejljcDVkMHU0Mzg5Zmd2cjBxcjhxOGF1ZXJvbSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/3ohze0QxPtkWu87rmU/giphy.gif" alt="Arabic calligraphy animation"> Project Documents

Research notes, reports, and graduation deliverables are maintained separately in [El-Maktab/baligh-documents](https://github.com/El-Maktab/baligh-documents).
