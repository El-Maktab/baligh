"""Dataset export utilities."""

import json
from pathlib import Path

from src.services.gec.modules.edit_tagger.common import ProjectedExample


class DatasetExporter:
    """Exports projected examples to dataset files."""

    def export_jsonl(
        self,
        examples: ProjectedExample,
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
            record = {
                "subwords": examples.subwords,
                "labels": examples.labels,
                "labels_star": examples.labels_star,
            }
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
            )
            file.write("\n")
