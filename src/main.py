"""Main entry point for Baligh.

Currently runs as a simple interactive REPL that reads Arabic text from stdin,
runs the full preprocessing pipeline, and prints the JSON output.
"""

import json
import sys

from src.services.ged.features.subsystems.rule_based.detector import RuleBasedDetector
from src.services.ged.orchestrator import GEDService
from src.services.ged.schemas import GEDInput
from src.services.preprocessing import (
    PreprocessingInput,
    preprocess,
)


def main() -> None:
    """Interactive REPL: reads Arabic text, runs preprocessing, and GED prints JSON."""
    print("Baligh - interactive mode")
    print("Type Arabic text and press Enter. Press Ctrl+C or Ctrl+D to exit.\n")

    while True:
        try:
            text = input("Enter text: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye bye.")
            sys.exit(0)

        if not text:
            continue

        result = preprocess(PreprocessingInput(text=text))

        detector = RuleBasedDetector()
        ged_service = GEDService(subsystems=[detector])

        ged_result = ged_service.process(
            GEDInput(
                text=result.text,
                normalized_text=result.normalized_text,
                tokens=result.tokens,
                morph_features=result.morph_features,
            )
        )

        # Pretty-print JSON (Pydantic model -> dict -> JSON string)
        print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))

        if ged_result.errors:
            print("*" * 40)
            print("GED Errors:")
            for i, error in enumerate(ged_result.errors, 1):
                print("*" * 20, f" Error {i} ", "*" * 20)
                print(f"  Error in: {text[error.span[0] : error.span[1]]}")
                print(f"  Error type: {error.category}:{error.subtype}")
                print(f"  Error explanation: {error.explanation_text}")

            print("*" * 40)
        print()


if __name__ == "__main__":
    main()
