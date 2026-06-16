"""Word and character-level alignment using dynamic programming."""

from src.services.gec.schemas import EditOperation
from src.services.gec.utils.distance_utils import levenshtein

from .common import Alignment, AlignmentType, BackPointer


class Aligner:
    """Aligns two lists of words using dynamic programming."""

    INSERT_DELETE_COST = 1
    REPLACE_COST = 2
    MERGE_COST = 1
    SPLIT_COST = 1

    def align_words(self, source: str, target: str) -> list[Alignment]:
        """Aligns two words and returns a list of Alignment."""
        source_list = source.split(" ") if source else []
        target_list = target.split(" ") if target else []

        _, parent = self._build_dp(source_list, target_list)
        return self._backtrack(source_list, target_list, parent, AlignmentType.WORD)

    def align_characters(self, source: str, target: str) -> list[Alignment]:
        """Aligns two strings at character level."""
        source_chars = list(source)
        target_chars = list(target)

        _, parent = self._build_dp(source_chars, target_chars)
        return self._backtrack(
            source_chars, target_chars, parent, AlignmentType.CHARACTER
        )

    def _word_cost(self, source_word: str, target_word: str) -> float:
        """Computes the cost of replacing source_word with target_word."""
        if source_word == target_word:
            return 0.0

        distance = levenshtein(source_word, target_word)
        return distance

    def _merge_cost(self, left: str, right: str, target: str) -> float:
        """Computes the cost of merging left and right into target."""
        merged = left + right
        return self._word_cost(merged, target)

    def _merge_cost_multiple(self, source_words: list[str], target: str) -> float:
        """Computes the cost of merging multiple source words into one target."""
        merged = "".join(source_words)
        return self._word_cost(merged, target)

    def _split_cost(self, source: str, left: str, right: str) -> float:
        """Computes the cost of splitting source into left and right."""
        split_target = left + right
        return self._word_cost(source, split_target)

    def _split_cost_multiple(self, source: str, target_words: list[str]) -> float:
        """Computes the cost of splitting source into multiple target words."""
        split_target = "".join(target_words)
        return self._word_cost(source, split_target)

    def _build_dp(
        self,
        source: list[str],
        target: list[str],
    ) -> tuple[list[list[float]], list[list[BackPointer | None]]]:
        """Builds the DP table and parent pointers for the given source and target."""
        n = len(source)
        m = len(target)

        dp = [[float("inf")] * (m + 1) for _ in range(n + 1)]
        parent: list[list[BackPointer | None]] = [
            [None] * (m + 1) for _ in range(n + 1)
        ]
        dp[0][0] = 0

        for i in range(1, n + 1):
            dp[i][0] = dp[i - 1][0] + self.INSERT_DELETE_COST * len(source[i - 1])
            parent[i][0] = BackPointer(EditOperation.DELETE, i - 1, 0)

        for j in range(1, m + 1):
            dp[0][j] = dp[0][j - 1] + self.INSERT_DELETE_COST * len(target[j - 1])
            parent[0][j] = BackPointer(EditOperation.INSERT, 0, j - 1)

        for i in range(1, n + 1):
            for j in range(1, m + 1):
                # KEEP && REPLACE
                replace_cost = dp[i - 1][j - 1] + self._word_cost(
                    source[i - 1], target[j - 1]
                )
                if replace_cost < dp[i][j]:
                    dp[i][j] = replace_cost

                    op = (
                        EditOperation.KEEP
                        if source[i - 1] == target[j - 1]
                        else EditOperation.REPLACE
                    )
                    parent[i][j] = BackPointer(op, i - 1, j - 1)

                # DELETE
                delete_cost = dp[i - 1][j] + self.INSERT_DELETE_COST * len(
                    source[i - 1]
                )
                if delete_cost < dp[i][j]:
                    dp[i][j] = delete_cost

                    parent[i][j] = BackPointer(EditOperation.DELETE, i - 1, j)

                # INSERT
                insert_cost = dp[i][j - 1] + self.INSERT_DELETE_COST * len(
                    target[j - 1]
                )
                if insert_cost < dp[i][j]:
                    dp[i][j] = insert_cost

                    parent[i][j] = BackPointer(EditOperation.INSERT, i, j - 1)

                # MERGE
                best_merge_cost = float("inf")
                best_merge_k = 0
                for k in range(2, i + 1):
                    source_words = source[i - k : i]
                    merge_cost = dp[i - k][j - 1] + self._merge_cost_multiple(
                        source_words, target[j - 1]
                    )

                    if merge_cost < best_merge_cost:
                        best_merge_cost = merge_cost
                        best_merge_k = k
                    else:
                        break

                if best_merge_cost < dp[i][j]:
                    dp[i][j] = best_merge_cost
                    parent[i][j] = BackPointer(
                        EditOperation.MERGE, i - best_merge_k, j - 1
                    )

                # SPLIT
                best_split_cost = float("inf")
                best_split_k = 0
                for k in range(2, j + 1):
                    target_words = target[j - k : j]
                    split_cost = dp[i - 1][j - k] + self._split_cost_multiple(
                        source[i - 1], target_words
                    )

                    if split_cost < best_split_cost:
                        best_split_cost = split_cost
                        best_split_k = k
                    else:
                        break

                if best_split_cost < dp[i][j]:
                    dp[i][j] = best_split_cost
                    parent[i][j] = BackPointer(
                        EditOperation.SPLIT, i - 1, j - best_split_k
                    )

        return dp, parent

    def _backtrack(self, source, target, parent, alignment_type: AlignmentType):
        """Backtrack through parent pointers to construct alignments.

        Backtracks through the parent pointers to construct the list of
        Alignment objects.
        """
        i = len(source)
        j = len(target)

        alignments = []
        while i > 0 or j > 0:
            ptr = parent[i][j]
            op = ptr.operation
            label = target[j - 1] if j > 0 else None

            if op in (EditOperation.KEEP, EditOperation.REPLACE):
                if op == EditOperation.KEEP:
                    label = None
                alignments.append(
                    Alignment(
                        source_start=i - 1,
                        source_end=i - 1,
                        target_start=j - 1,
                        target_end=j - 1,
                        operation=op,
                        label=label,
                        alignment_type=alignment_type,
                    )
                )

            elif op == EditOperation.MERGE:
                alignments.append(
                    Alignment(
                        source_start=ptr.prev_i,
                        source_end=i - 1,
                        target_start=j - 1,
                        target_end=j - 1,
                        operation=op,
                        alignment_type=alignment_type,
                    )
                )

            elif op == EditOperation.SPLIT:
                alignments.append(
                    Alignment(
                        source_start=i - 1,
                        source_end=i - 1,
                        target_start=ptr.prev_j,
                        target_end=j - 1,
                        operation=op,
                        alignment_type=alignment_type,
                    )
                )

            elif op == EditOperation.DELETE:
                alignments.append(
                    Alignment(
                        source_start=i - 1,
                        source_end=i - 1,
                        target_start=j,
                        target_end=j - 1,
                        operation=op,
                        alignment_type=alignment_type,
                    )
                )

            elif op == EditOperation.INSERT:
                alignments.append(
                    Alignment(
                        source_start=i,
                        source_end=i - 1,
                        target_start=j - 1,
                        target_end=j - 1,
                        operation=op,
                        label=label,
                        alignment_type=alignment_type,
                    )
                )

            i = ptr.prev_i
            j = ptr.prev_j

        alignments.reverse()
        return alignments
