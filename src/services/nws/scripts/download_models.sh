#!/bin/bash
set -e

# ==============================================================================
# Usage:
#   ./src/services/nws/scripts/download_models.sh
#
# Description:
#   Downloads the NWS models from Hugging Face into the data directory.
#   Automatically skips already downloaded files.
# ==============================================================================

# Define the target directory relative to the project root
TARGET_DIR="src/services/nws/data"

# Ensure the target directory exists
mkdir -p "$TARGET_DIR"

echo "📥 Checking for huggingface-cli..."
if ! uv run which huggingface-cli > /dev/null 2>&1; then
    echo "⚙️ huggingface-cli not found in the environment. Installing huggingface_hub..."
    uv pip install "huggingface_hub[cli]"
fi

echo "📥 Downloading NWS models from Hugging Face..."
echo "📂 Target directory: $TARGET_DIR"
echo "--------------------------------------------------------"

# Use huggingface-cli to download the entire repository.
# The --local-dir flag automatically checks existing files and skips them if they are already downloaded.
# We set --local-dir-use-symlinks False to ensure actual files are placed in the directory, not symlinks.
uv run huggingface-cli download akramhany65/nws_models \
    --repo-type model \
    --local-dir "$TARGET_DIR" \
    --local-dir-use-symlinks False

echo "--------------------------------------------------------"
echo "✅ Download complete! Models are ready in $TARGET_DIR"
