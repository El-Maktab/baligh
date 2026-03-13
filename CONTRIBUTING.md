# Contributing to Baligh

This document outlines the conventions and guidelines to follow when working on this project (Discuss if we need to update)

---

## Table of Contents

- [Contributing to Baligh](#contributing-to-baligh)
  - [Table of Contents](#table-of-contents)
  - [File Structure](#file-structure)
    - [Module Structure](#module-structure)
  - [Preferred Tooling](#preferred-tooling)
  - [Branch Conventions](#branch-conventions)
  - [Commit Conventions](#commit-conventions)
    - [Types](#types)
    - [Scopes](#scopes)

---

## File Structure

```sh
baligh/
├── assets/                  # Static assets
├── clients/
│   ├── extension/           # Browser extension client
│   └── web/                 # Web front-end client
├── docs/                    # Technical documentation
├── src/
│   ├── api/                 # API layer (routing, request/response handling)
│   ├── core/                # Integration core for all services, shared utilities
│   └── services/
│       ├── explanation/     # Correction explanation generation
│       ├── gec/             # Grammatical Error Correction
│       ├── ged/             # Grammatical Error Detection
│       ├── nws/             # Next Word Suggestion
│       ├── ontology/        # Arabic ontology / lexical resources
│       ├── preprocessing/   # All A-NLP preprocessing pipelines and utilities
│       └── utils/           # Shared utilities used across services
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

### Module Structure

The structure of each service module is inspired by [anesriad/Telco-Customer-Churn-ML](https://github.com/anesriad/Telco-Customer-Churn-ML/tree/main).

Each service under `src/services/` follows this internal layout:

```sh
<service>/
├── app/          # Service entry point and application wiring
├── data/         # Data loading, datasets, and raw/processed data handling
├── features/     # Feature engineering and transformation pipelines
├── models/       # train, evaluate, tune scripts
├── notebooks/    # Exploratory notebooks, for experimentation and analysis
├── serving/      # Inference logic and model serving
└── utils/        # Helper functions specific to this service
```

---

## Preferred Tooling

When possible, prefer the following tools in this project:

- `uv` for Python environment and dependency management.
  Docs: <https://docs.astral.sh/uv/>
- `Great Expectations` for data validation and data quality checks.
  Docs: <https://docs.greatexpectations.io/docs/home>
- `MLflow` for tracking and recording all experiments.
  Docs: <https://mlflow.org/docs/latest/index.html>
- `FastAPI` for backend/API implementation.
  Docs: <https://fastapi.tiangolo.com/>

---

## Branch Conventions

Branches follow the pattern: `<type>/<short-description>`

Use lowercase and hyphens only (no spaces, no underscores).

| Type          | When to use                                    |
| ------------- | ---------------------------------------------- |
| `feat/`       | New feature or capability                      |
| `fix/`        | Bug fix                                        |
| `chore/`      | Tooling, config, build, or scaffolding changes |
| `docs/`       | Documentation only changes                     |
| `refactor/`   | Code restructuring with no behaviour change    |
| `experiment/` | Research spikes or exploratory work            |

**Examples:**

```
chore/project-bootstrap
feat/gec-rule-based-pipeline
fix/api-timeout-handling
docs/update-contributing-guide
experiment/arabert-finetuning
```

---

## Commit Conventions

Commits follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<optional scope>): <short description>
```

- Use the **imperative mood** in the description ("add", not "added" or "adds")

### Types

| Type       | When to use                                                 |
| ---------- | ----------------------------------------------------------- |
| `feat`     | Introduces a new feature                                    |
| `fix`      | Fixes a bug                                                 |
| `chore`    | Maintenance, tooling, or config (no production code change) |
| `docs`     | Documentation changes only                                  |
| `refactor` | Restructuring code without changing behaviour               |
| `test`     | Adding or updating tests                                    |
| `perf`     | Performance improvements                                    |
| `ci`       | CI/CD configuration changes                                 |

### Scopes

Scope is optional but encouraged. Use the relevant module or directory name:

`gec`, `ged`, `nws`, `explanation`, `ontology`, `preprocessing`, `api`, `core`, `web`, `extension`

**Examples:**

```
feat(gec): add rule-based agreement checker
fix(api): handle empty input payloads gracefully
docs: add contributing guide
chore(preprocessing): scaffold tokenizer module
refactor(core): extract shared Arabic text utilities
```

---
