"""Dataset export utilities."""

import json
from pathlib import Path

from src.services.gec.modules.edit_tagger.common import ProjectedExample


class DatasetExporter:
    """Exports projected examples to dataset files."""

    def export_jsonl(
        self,
        examples: list[ProjectedExample],
        output_path: Path,
    ) -> None:
        """Export examples to a JSONL file.

        Args:
            examples: Projected examples to export.
            output_path: Destination file path.
        """
        with output_path.open(
            mode="w",
            encoding="utf-8",
        ) as file:
            for example in examples:
                record = {
                    "tokens": example.tokens,
                    "labels": example.labels,
                }

                file.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                    )
                )
                file.write("\n")