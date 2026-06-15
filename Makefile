.PHONY: help install format lint type-check test all clean camel-data pre-commit

# Default target
help:
	@echo "Baligh Development Commands"
	@echo "============================"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install all dependencies"
	@echo "  make camel-data    Download CAMeL Tools data (morphology & disambiguation)"
	@echo "  make ged-dict      Download dictionaries from our drive"
	@echo ""
	@echo "Quality Checks:"
	@echo "  make format        Format code with ruff"
	@echo "  make lint          Lint code with ruff"
	@echo "  make type-check    Type check with mypy"
	@echo "  make test          Run tests with pytest"
	@echo "  make all           Run format, lint, type-check, and tests"
	@echo ""
	@echo "Other:"
	@echo "  make clean         Remove temporary files and caches"
	@echo "  make pre-commit    Run pre-commit hooks on all files"
	@echo ""

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
ged-dict:
	@echo "Downloading GED dictionaries..."
	uv run --with gdown gdown -O src/services/ged/features/subsystems/lexicon/dictionary 1XnAZL1chShOsus-qoqDJLcGzbq_pngPg
	uv run --with gdown gdown -O src/services/ged/features/subsystems/lexicon/dictionary 1SulNK5S4KfNZSiVFu047GncG84QyoKlv

# Format code
format:
	@echo "Formatting code with ruff..."
	uv run ruff format .

# Lint code
lint:
	@echo "Linting code with ruff..."
	uv run ruff check .

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

# Format check (without fixing) - useful for CI
format-check:
	@echo "Checking format with ruff..."
	uv run ruff format --check .
