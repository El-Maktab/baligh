"""Parser for parallel GEC corpora."""

from pathlib import Path

from src.services.gec.modules.edit_tagger.common import ParallelExample


class ParallelCorpusParser:
    """Parses source/target parallel corpora into ParallelExample objects."""

    def parse(
        self,
        source_path: Path,
        target_path: Path,
    ) -> list[ParallelExample]:
        """Parse parallel corpus files.

        Args:
            source_path: Path to source sentences.
            target_path: Path to corrected sentences.

        Returns:
            List of parsed parallel examples.

        Raises:
            ValueError: If source and target files contain different
                numbers of lines.
        """
        source_lines: list[str] = []
        target_lines: list[str] = []

        with source_path.open(encoding="utf-8") as source_file:
            source_lines = [
                line.strip().split(maxsplit=1)[1]
                for line in source_file
                if line.strip()
            ]

        with target_path.open(encoding="utf-8") as target_file:
            target_lines = [
                line.strip().split(maxsplit=1)[1]
                for line in target_file
                if line.strip()
            ]

        if len(source_lines) != len(target_lines):
            raise ValueError(
                "Source and target files contain different numbers of lines."
            )

        examples: list[ParallelExample] = []

        for source_line, target_line in zip(source_lines, target_lines, strict=True):
            examples.append(
                ParallelExample(
                    source=source_line,
                    target=target_line,
                )
            )

        return examples
