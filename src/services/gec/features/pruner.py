"""Label pruning utilities."""

from collections import Counter

from src.services.gec.modules.edit_tagger.common import ProjectedExample


class LabelPruner:
    """Prunes infrequent labels from training examples."""

    def __init__(
        self,
        min_frequency: int,
        default_label: str = "K",
    ) -> None:
        """Initialize the pruner.

        Args:
            min_frequency: Minimum number of occurrences required
                for a label to be retained.
            default_label: Replacement label for pruned labels.
        """
        self.min_frequency = min_frequency
        self.default_label = default_label

    def prune(
        self,
        examples: list[ProjectedExample],
    ) -> list[ProjectedExample]:
        """Replace rare labels with the default label.

        Args:
            examples: Training examples.

        Returns:
            Examples with rare labels replaced.
        """
        label_counts: Counter[str] = Counter()

        for example in examples:
            label_counts.update(example.labels_star)

        # min_label, min_count = min(
        #     label_counts.items(),
        #     key=lambda item: item[1]
        # )

        # print("min: ", min_label, min_count)

        rare_labels = {
            label for label, count in label_counts.items() if count < self.min_frequency
        }
        print("total: ", len(label_counts))
        print("rare: ", len(rare_labels))
        pruned_examples: list[ProjectedExample] = []

        for example in examples:
            pruned_labels = [
                self.default_label if label in rare_labels else label
                for label in example.labels
            ]

            pruned_examples.append(
                ProjectedExample(
                    subwords=example.subwords,
                    labels=[
                        self.default_label if label in rare_labels else label
                        for label in example.labels_star
                    ] if example.labels_star is not None else None,
                    labels_star= pruned_labels
                )
            )
        
        return pruned_examples
