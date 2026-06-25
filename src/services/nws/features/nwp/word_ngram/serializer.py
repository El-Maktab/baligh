"""Serialization utilities for the Word N-Gram LM.

MsgPack requires string keys for dictionaries. This module handles converting
integer IDs and tuple[int, ...] contexts into strings and back.
"""

import gzip
import logging
from pathlib import Path
from typing import Any

import msgpack

logger = logging.getLogger(__name__)


def save_ngram_model(model_data: dict[int, Any], path: str | Path) -> None:
    """Save the integerized model to a gzipped msgpack file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    serializable_data: dict[str, Any] = {}

    for n, order_data in model_data.items():
        if n == 1:
            # Convert int keys to str
            serializable_data[str(n)] = {str(k): v for k, v in order_data.items()}
        else:
            serializable_order_data = {}
            for context, data in order_data.items():
                # Convert tuple[int, ...] to a comma-separated string
                ctx_str = ",".join(str(i) for i in context)

                # Convert target ints in "probs" to str
                str_probs = {str(k): v for k, v in data["probs"].items()}

                serializable_order_data[ctx_str] = {
                    "lambda": data["lambda"],
                    "probs": str_probs,
                }
            serializable_data[str(n)] = serializable_order_data

    logger.info(f"Saving word n-gram model to {path}...")
    with gzip.open(path, "wb") as f:
        packed = msgpack.packb(serializable_data, use_bin_type=True)
        f.write(packed)  # type: ignore
    logger.info("Model saved successfully.")


def load_ngram_model(path: str | Path) -> dict[int, Any]:
    """Load the integerized model and restore ints and tuples."""
    path = Path(path)
    logger.info(f"Loading word n-gram model from {path}...")

    with gzip.open(path, "rb") as f:
        packed = f.read()

    serializable_data = msgpack.unpackb(packed, raw=False)

    model_data: dict[int, Any] = {}
    for n_str, order_data in serializable_data.items():
        n = int(n_str)
        if n == 1:
            model_data[n] = {int(k): v for k, v in order_data.items()}
        else:
            restored_order_data = {}
            for ctx_str, data in order_data.items():
                context: tuple[int, ...] = eval(ctx_str)

                int_probs = {int(k): v for k, v in data["probs"].items()}

                restored_order_data[context] = {
                    "lambda": data["lambda"],
                    "probs": int_probs,
                }
            model_data[n] = restored_order_data

    logger.info("Model loaded successfully.")
    return model_data
