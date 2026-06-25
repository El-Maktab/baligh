"""Serialization utilities for the Character N-gram LM.

Authors:
    - Akram Hany
"""

import gzip
import logging
from pathlib import Path
from typing import Any

import msgpack

logger = logging.getLogger(__name__)


def save_model(model_data: dict[int, Any], path: str | Path) -> None:
    """Save the smoothed model to a gzipped msgpack file.

    Converts integer keys and tuple contexts to strings to comply with
    msgpack key requirements, and for compact storage.

    Args:
        model_data: The nested dictionary produced by KneserNeySmoother.
        path: Path to save the `.msgpack.gz` file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    serializable_data: dict[str, Any] = {}

    for n, order_data in model_data.items():
        if n == 1:
            serializable_data[str(n)] = order_data
        else:
            # Convert context tuples to strings
            serializable_order_data = {}
            for context, data in order_data.items():
                ctx_str = "".join(context)
                serializable_order_data[ctx_str] = data
            serializable_data[str(n)] = serializable_order_data

    logger.info(f"Saving character n-gram model to {path}...")
    with gzip.open(path, "wb") as f:
        # type-ignore is needed because msgpack.packb returns bytes, which gzip accepts
        packed = msgpack.packb(serializable_data, use_bin_type=True)
        f.write(packed)  # type: ignore
    logger.info("Model saved successfully.")


def load_model(path: str | Path) -> dict[int, Any]:
    """Load the smoothed model from a gzipped msgpack file.

    Reconstructs the original dictionary structure, parsing context strings
    back into tuples for the runtime model to use.

    Args:
        path: Path to the `.msgpack.gz` file.

    Returns:
        The model data dictionary, formatted exactly as smoother.build_model() outputs.
    """
    path = Path(path)
    logger.info(f"Loading character n-gram model from {path}...")

    with gzip.open(path, "rb") as f:
        packed = f.read()

    serializable_data = msgpack.unpackb(packed, raw=False)

    model_data: dict[int, Any] = {}
    for n_str, order_data in serializable_data.items():
        n = int(n_str)
        if n == 1:
            model_data[n] = order_data
        else:
            # Convert context strings back to tuples
            restored_order_data = {}
            for ctx_str, data in order_data.items():
                # Each character is an element of the tuple
                context = tuple(ctx_str)
                restored_order_data[context] = data
            model_data[n] = restored_order_data

    logger.info("Model loaded successfully.")
    return model_data
