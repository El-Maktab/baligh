.PHONY: \
	help install format lint type-check test all clean pre-commit \
	camel-data ged-dict-download ged-lexicon ged-ml-datasets \
	ged-ml-model-download ged-eval-datasets ged-evaluate ged-setup-prod \
	nws-model-download

# Default target
help:
	@echo "Baligh Development Commands"
	@echo "============================"
	@echo ""
	@echo "Setup:"
	@echo "  make setup                 Setup development environment"
	@echo "  make install               Install all dependencies"
	@echo "  make camel-data            Download CAMeL Tools data (morphology & disambiguation)"
	@echo "  make ged-dict-download     Download dictionaries from our drive"
	@echo "  make ged-lexicon           Build processed GED lexicon trie resources"
	@echo "  make ged-ml-model-download Download a pinned Hugging Face model"
	@echo "  make nws-model-download    Download NWS models from Hugging Face"
	@echo "  make text-editing-models   Download text editing models from Drive"
	@echo "  make ged-setup-prod        Prepare GED runtime dependencies for production"
	@echo ""
	@echo "GED commands:"
	@echo "  make ged-evaluate          Evaluate all GED detectors"
	@echo "  make ged-eval-datasets     Download GED evaluation datasets from our drive"
	@echo "  make ged-ml-datasets       Download GED ML datasets"
	@echo ""
	@echo "Quality Checks:"
	@echo "  make format                Format code with ruff"
	@echo "  make lint                  Lint code with ruff"
	@echo "  make type-check            Type check with mypy"
	@echo "  make test                  Run tests with pytest"
	@echo "  make all                   Run format, lint, type-check, and tests"
	@echo ""
	@echo "Other:"
	@echo "  make clean                 Remove temporary files and caches"
	@echo "  make pre-commit            Run pre-commit hooks on all files"
	@echo "  make run                   Run a Python script (usage: make run SCRIPT=src/...)"
	@echo "  make run-api               Run the API server"
	@echo ""

setup: install camel-data ged-setup-prod nws-model-download
	@echo "Baligh setup done"


# Install dependencies
install:
	@echo "Installing dependencies..."
	uv sync --group dev

# Download CAMeL Tools data
camel-data:
	@echo "Downloading CAMeL Tools data..."
	uv run camel_data -i morphology-db-msa-r13
	uv run camel_data -i disambig-mle-calima-msa-r13

# Download GED dictionaries
ged-dict-download:
	@echo "Downloading GED dictionaries..."
	uv run --with gdown gdown -O src/services/ged/detectors/lexicon/dictionary/ 1XnAZL1chShOsus-qoqDJLcGzbq_pngPg
	uv run --with gdown gdown -O src/services/ged/detectors/lexicon/dictionary/ 1SulNK5S4KfNZSiVFu047GncG84QyoKlv

# Download GED ml datasets
ged-ml-datasets:
	@echo "Downloading GED ML datasets..."
	uv run --with gdown gdown -O src/services/ged/data/ml/qalb14/ 1QnhPR4LCfT2oG92VtnWHZWSuaPrcUVoM
	unzip -o ./src/services/ged/data/ml/qalb14/baligh-ged-qalb14-wo-camelira-coarse-v0.1.0.zip -d ./src/services/ged/data/ml/qalb14/

# Download the pinned model bundle.
ged-ml-model-download:
	uv run --with huggingface-hub hf download "amirkedis/baligh-ged-crf-morph" \
		--repo-type model \
		--local-dir "artifacts/ged/ml/crf-surface-morph-v2/v0.2.0"

# Download NWS models
nws-model-download:
	@mkdir -p src/services/nws/data
	uv run --with huggingface-hub hf download akramhany65/nws_models \
		--repo-type model \
		--local-dir src/services/nws/data
	@echo "Download complete! Models are ready in src/services/nws/data"

# Download text editing models
text-editing-models:
	@echo "Downloading text editing models..."
	uv run --with gdown gdown -O src/services/gec/models/ --folder 1ilLnP8Dt_cSGPzwhFmbq8K8I7XJTMgzu
	@echo "Download complete! Models are ready in src/services/gec/models/"

# Prepare GED runtime dependencies
ged-setup-prod: ged-dict-download ged-lexicon ged-ml-model-download
	@echo "GED production setup complete!"

# Download GED evaluation datasets
ged-eval-datasets:
	@echo "Downloading GED evaluation datasets..."
	uv run --with gdown gdown -O src/services/ged/data/evaluation/ 1xy-FKY6mKAztAex7e1r0m9wTUda3yY63
	unzip -o ./src/services/ged/data/evaluation/baligh-ged-eval-datasets-v0.1.0.zip -d ./src/services/ged/data/evaluation/

# Evaluate the three GED detectors and their fused output.
ged-evaluate:
	uv run python -m src.services.ged.evaluation

# Build processed GED lexicon tries
ged-lexicon:
	@echo "Building GED lexicon trie resources..."
	uv run python -m src.services.ged.detectors.lexicon.processor

# Format code
format:
	@echo "Formatting code with ruff..."
	uv run ruff format .

# Check linting
lint:
	@echo "Linting code with ruff..."
	uv run ruff check .

# Lint code
lint-fix:
	@echo "Linting code with ruff..."
	uv run ruff check --fix .

# Type check
type-check:
	@echo "Type checking with mypy..."
	uv run mypy

# Run tests
test:
	@echo "Running tests with pytest..."
	uv run pytest

# Run all quality checks
all: format lint type-check test
	@echo "✓ All quality checks passed!"

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned!"

# Run pre-commit hooks
pre-commit:
	@echo "Running pre-commit hooks..."
	uv run pre-commit run --all-files

# Run a Python script with project root on PYTHONPATH
run:
	@echo "Running $(SCRIPT)..."
	PYTHONPATH=. uv run python $(SCRIPT)

# Run the API server
run-api:
	@echo "Running API server..."
	uv run uvicorn src.api.app:app --reload

# Format check (without fixing) - useful for CI
format-check:
	@echo "Checking format with ruff..."
	uv run ruff format --check .
