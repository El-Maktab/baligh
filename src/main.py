"""Main entry point for Baligh.

Currently runs as a simple interactive REPL that reads Arabic text from stdin,
runs the full preprocessing pipeline, and prints the JSON output.
"""

import json
import sys

from src.services.preprocessing import (
    PreprocessingInput,
    preprocess,
)


def main() -> None:
    """Interactive REPL: reads Arabic text, runs preprocessing, prints JSON."""
    print("Baligh Preprocessing - interactive mode")
    print("Type Arabic text and press Enter. Press Ctrl+C or Ctrl+D to exit.\n")

    while True:
        try:
            text = input("Enter text: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbyebye.")
            sys.exit(0)

        if not text:
            continue

        result = preprocess(PreprocessingInput(text=text))

        # Pretty-print JSON (Pydantic model -> dict -> JSON string)
        print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
        print()


if __name__ == "__main__":
    main()
