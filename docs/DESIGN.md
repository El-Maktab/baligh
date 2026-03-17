# Baligh: System Design & Architecture

> **Arabic Writing Assistant** — Graduation Project, Cairo University, Computer Engineering Department

---

## Overview

Baligh is an MSA (Modern Standard Arabic) writing assistant providing real-time **Grammatical Error Correction (GEC)** and **Next-Word Suggestion (NWS)** with high accuracy and low latency.

---

## High-Level Architecture

```
┌─────────────────┐     ┌──────────────────────────────┐
│   CLIENT LAYER  │     │      PREPROCESSING PIPELINE   │
│                 │────▶│  Text Cleaning → Segmentation │
│  User Interface │     │  (Farasa) → Morphological     │
│  / API Endpoint │     │  Analysis (CAMeL) → Diacrit-  │
│                 │     │  ization                      │
└─────────────────┘     └──────────────┬───────────────┘
                                       │
                        ┌──────────────▼───────────────┐
                        │         CORE FEATURES         │
                        │  ┌────────────────────────┐  │
                        │  │   GED Module           │  │
                        │  │   (Error Detection)    │  │
                        │  └────────────┬───────────┘  │
                        │  ┌────────────▼───────────┐  │
                        │  │  Explanation /         │  │
                        │  │  Fusion Layer          │──┼──▶ Slow Path
                        │  └────────────────────────┘  │
                        │  ┌────────────────────────┐  │
                        │  │   GIEC Module          │  │
                        │  │   (Correction)         │  │
                        │  └────────────────────────┘  │
                        │  ┌────────────────────────┐  │
                        │  │   NWS Module           │──┼──▶ Fast Path
                        │  │   (Next Word)          │  │
                        │  └────────────────────────┘  │
                        └──────────────────────────────┘
```

**Output** (Slow Path): Highlighted errors, correction suggestions, word predictions, grammar rule citations.
**Output** (Fast Path): Top-K next word predictions, top-K word completions.

---

## Module Breakdown

### 1. Preprocessing Module (10%)

**Function:** Text cleaning, normalization, tokenization, and morphological analysis.

| Stage | Tool/Method |
|---|---|
| Text Cleaning | Normalization rules |
| Segmentation | Farasa |
| Morphological Analysis | CAMeL |
| Diacritization | Diacritization model |

- **Input:** Raw Arabic text from the user
- **Output:** Tokenized text + Morphological features (POS tags, syntactic parse, Lemma)

---

### 2. GED Engine — Grammatical Error Detection (20%)

**Function:** Detects grammatical errors using a fusion of rule-based, pattern-based, and ML approaches.

```
                         ┌─────────────────────┐
                         │  DETECTION MODULES  │
Preprocessing            │  ┌───────────────┐  │    ┌──────────────────┐
Output ─────────────────▶│  │ Rule-Based    │  │    │  FUSION &        │
                         │  │ Checker       │──┼───▶│  DECISION        │
                         │  └───────────────┘  │    │                  │
                         │  ┌───────────────┐  │    │  ┌────────────┐  │
                         │  │ Pattern-Based │──┼───▶│  │Fusion Layer│  │──▶ Classified
                         │  │ Matcher       │  │    │  └─────┬──────┘  │    Errors
                         │  └───────────────┘  │    │        │         │
                         │  ┌───────────────┐  │    │  ┌─────▼──────┐  │
                         │  │ Sequence      │──┼───▶│  │Priority    │  │
                         │  │ Labeler (ML)  │  │    │  │Logic       │  │
                         │  └───────────────┘  │    │  └────────────┘  │
                         └─────────────────────┘    └──────────────────┘
```

- **Input:** Preprocessed text
- **Output:** Final error list with confidence scores and explanations

---

### 3. GEC — Ontology & Dictionary-Based Correction (20%)

**Function:** Generates correction candidates using a grammar ontology (for grammatical errors) and a dictionary lookup (for spelling errors).

```
                         ┌──────────────────────────────┐
                         │    CORRECTION STRATEGIES     │
Preprocessing &          │  ┌────────────────────────┐  │
GED Outputs ────────────▶│  │ Ontology-Based         │  │
                         │  │ (Explainable)          │──┼──▶ ┌─────────────┐
                         │  └────────────────────────┘  │    │  RANKING &  │
                         │  ┌────────────────────────┐  │    │  EXPLANATION│
                         │  │ Dictionary Lookup      │──┼──▶ │             │──▶ Corrections
                         │  │ (Spelling)             │  │    │  Candidate  │
                         │  └────────────────────────┘  │    │  Ranker     │
                         │  ┌────────────────────────┐  │    └─────────────┘
                         │  │ Text Editing Based     │──┼──▶
                         │  │ (ML)                   │  │
                         │  └────────────────────────┘  │
                         └──────────────────────────────┘
```

- **Input:** Preprocessed text
- **Output:** Correction candidates

---

### 4. GEC — Text Editing & Ranking (15%)

**Function:** Applies a text-editing ML approach to the correction candidates, ranks them, and generates human-readable explanations.

- **Input:** Preprocessed text + Module 3 correction candidates
- **Output:** Final ranked corrections with explanations

---

### 5. NWS Module — Next Word Suggestion (30%)

**Function:** Predicts the next word (NWP) or completes the current word being typed (WAC) using a smart caching layer and context-aware re-ranking.

```
┌───────────────────────────────────────────────────────────────────────┐
│  SMART CACHE LAYER         LOGIC CONTROL          PREPROCESSING       │
│  ┌──────────────┐          ┌──────────┐           ┌────────────────┐  │
│  │ Idioms Cache │          │ Cache    │    No      │ Normalization  │  │
│  └──────────────┘          │ Hit?  ───┼───────────▶ → Tokenizer    │  │
│  ┌──────────────┐          └────┬─────┘           └───────┬────────┘  │
│  │Famous Phrases│               │ Yes                     │           │
│  └──────────────┘          ┌────▼──────────┐    ┌─────────▼────────┐ │
│  ┌──────────────┐          │Return Cached  │    │  MODE DETECTION   │ │
│  │User Patterns │          │Result         │    │  Space? → NWP     │ │
│  │(LRU)         │          └───────────────┘    │  Typing? → WAC   │ │
│  └──────────────┘                               └─────────┬────────┘ │
└────────────────────────────────────────────────           │          │
                                                  ┌─────────▼────────┐ │
                     NWP Pipeline                 │  ┌─────────────┐ │ │
                 ┌───────────────────┐            │  │Next-Word    │ │ │──▶ Top-K Next Words
                 │ Next-Word         │◀───────────┤  │Prediction   │ │ │
                 │ Prediction Core   │            │  │Core         │ │ │
                 └───────────────────┘            │  └─────────────┘ │ │
                     WAC Pipeline                 │  ┌─────────────┐ │ │
                 ┌───────────────────┐            │  │Trie Lookup +│ │ │──▶ Top-K Completions
                 │ Trie Lookup +     │◀───────────┤  │Context-Aware│ │ │
                 │ Context-Aware     │            │  │Re-ranking   │ │ │
                 │ Re-ranking        │            │  └─────────────┘ │ │
                 └───────────────────┘            └──────────────────┘ │
```

- **Input:** Preprocessed text
- **Output:** Ranked list of predicted next words (NWP) + word completions (WAC)

---

### 6. API & GUI (20%)

**Function:** REST API backend + web frontend with live text editor.

- **Input:** User text input + outputs from all modules
- **Output:** Web UI with a live Arabic text editor (+ optional browser extension)

---

## Deliverables Summary

| # | Module | Function | % Libs |
|---|---|---|---|
| 1 | Preprocessing Module | Text cleaning, normalization, tokenization, morphological analysis | 10% |
| 2 | GED Engine | Error detection (Rules + Patterns + ML + Fusion) | 20% |
| 3 | GEC (Ontology & Dictionary-Based) | Correction candidates via grammar ontology + spelling dictionary | 20% |
| 4 | GEC (Text Editing & Ranking) | Text editing (ML) + candidate ranking + explanation generation | 15% |
| 5 | NWS Module | Next word suggestion (NWP + WAC) | 30% |
| 6 | API & GUI | REST API + Frontend web editor | 20% |

---

## Data Flow Summary

```
Raw Arabic Text
      │
      ▼
[1] Preprocessing
      │
      ├──▶ [2] GED Engine (Error Detection)
      │          │
      │          ├──▶ [3] GEC Ontology/Dict (Correction Candidates)
      │          │          │
      │          │          ▼
      │          │    [4] GEC Text Editing & Ranking ──▶ Final Corrections
      │          │
      │          └──▶ (error metadata for Explanation/Fusion Layer)
      │
      └──▶ [5] NWS Module ────────────────────────────▶ Word Predictions

[6] API & GUI ◀── collects outputs from all modules
      │
      ▼
   User (Web UI / Browser Extension)
```

---

## Design Decisions

A log of design questions discussed and the decisions made, with rationale.

---

### DD-001 — Should diacritization come before or after morphological analysis?

**Status:** Decided

**Options considered:**

| Option | Description |
|---|---|
| A — Diacritize first | Run a diacritizer on the raw/segmented text, then feed the diacritized text into the morphological analyzer |
| B — Morph analysis first | Run CAMeL to get multiple morphological candidates per token, then use diacritization to disambiguate |
| C — Joint (interleaved) | Treat them as a single step; CAMeL internally resolves both simultaneously |

**Decision: Option C (joint/interleaved) — effectively Option B in implementation.**

**Rationale:**

Diacritization and morphological analysis are **mutually dependent** — this is the fundamental chicken-and-egg problem in Arabic NLP:

- To diacritize correctly you need morphological context (is `كتب` a verb or a noun?).
- To pick the right morphological analysis you need the diacritization (which reading is correct in context?).

Modern tools like CAMeL handle this jointly: the morphological analyzer produces **multiple candidate analyses**, each with its own diacritized form, and a **disambiguation step** (context-aware, using the surrounding tokens) selects the best candidate. The winning candidate *is* the diacritization — they are resolved in one pass, not two sequential steps.

Running an independent diacritizer first (Option A) would be redundant and potentially harmful: it would force a single diacritization choice before the morphological analyzer has seen the context, and any error there propagates forward.

**Conclusion:** The pipeline step called "Diacritization" in the architecture is more precisely the **morphological disambiguation step** that is built into CAMeL. No separate diacritization model is needed before morph analysis. The order stays:

```
Segmentation (Farasa) → Morphological Analysis + Disambiguation (CAMeL) → resolved tokens with POS/lemma/diacritics
```

---

### DD-002 — How do we handle incomplete (still-being-typed) words in real-time input?

**Status:** Decided

**Problem:**
Input is instantaneous — the last token is almost always unfinished. Sending it through full preprocessing (segmentation, morphological analysis) is invalid since it's not a complete word yet. But we can't discard it either — it's exactly what the NWS/WAC pipeline needs.

**Decision: Split input at the last word boundary before preprocessing runs.**

**Word boundary signals** — a word is considered complete if followed by any delimiter:
- Whitespace (space, newline)
- Arabic punctuation: `، ؟ ؛`
- Latin/shared punctuation: `. , ! ? ; : " ' ( ) [ ] { } - —`

**Split logic:**

```
last char is Arabic letter/digit  →  incomplete fragment  →  split off last token  →  WAC mode
last char is any delimiter         →  all tokens complete  →  nothing to split       →  NWP mode
```

**Routing after the split:**

```
Input: "ذهب الطلاب إلى المدرس"

Completed prefix: "ذهب الطلاب إلى"
      │
      ▼
Full preprocessing (segmentation + morph analysis)
      │
      ├──▶ GED / GEC  (error detection stops at last completed token)
      └──▶ NWS        (provides sentence context for re-ranking)

Current fragment: "المدرس"
      │
      ▼
Light normalization only (e.g. alif variants: أ/إ/ا → canonical form)
      │
      └──▶ NWS / WAC  (trie lookup + context-aware re-ranking)
```

**Additional rules:**
- GED must never flag the current fragment — an unfinished word cannot be an error.
- Delimiters are word-completion signals but not context boundaries — the completed prefix flows as one unit into preprocessing regardless of internal punctuation.

**Deferred:** When the cursor is not at the end of the input (mid-sentence editing), the incomplete token is at the cursor position, not the last character. Detecting this requires the client to send a cursor offset alongside the text. This is a GUI/API layer concern and is out of scope for the preprocessing module.
