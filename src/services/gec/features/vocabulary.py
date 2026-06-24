"""Vocabulary building utilities."""

from src.services.gec.modules.edit_tagger.common import ProjectedExample


class LabelVocabularyBuilder:
    """Builds label vocabularies for edit tagging."""

    PAD_LABEL = "[PAD]"
    UNK_LABEL = "[UNK_EDIT]"

    def build(
        self,
        examples: list[ProjectedExample],
    ) -> tuple[dict[str, int], dict[int, str]]:
        """Build label-id mappings.

        Args:
            examples: Training examples.

        Returns:
            Tuple of:
                - label2id
                - id2label
        """
        unique_labels: set[str] = set()

        for example in examples:
            if example.labels_star is not None:
                unique_labels.update(example.labels_star)
            else:
                unique_labels.update(example.labels)

        sorted_labels = sorted(unique_labels)

        label2id: dict[str, int] = {
            self.PAD_LABEL: 0,
            self.UNK_LABEL: 1,
        }

        next_id = len(label2id)

        for label in sorted_labels:
            if label in label2id:
                continue

            label2id[label] = next_id
            next_id += 1

        id2label = {idx: label for label, idx in label2id.items()}

        return label2id, id2label
