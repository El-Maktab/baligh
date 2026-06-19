"""String distance and similarity utilities."""

from pyarabic.araby import (
    ALEFAT,
    HAMZAT,
    TEHLIKE,
    WAWLIKE,
    YEHLIKE,
)

_SIMILAR_COST = 0.3

_ARABIC_EQUIVALENCE_CLASSES: list[tuple[str, ...]] = [
    tuple(ALEFAT),
    tuple(HAMZAT),
    tuple(TEHLIKE),
    tuple(WAWLIKE),
    tuple(YEHLIKE),
    ("ة", "ه"),
    ("ي", "ى"),
]

_CHAR_TO_CLASSES: dict[str, set[int]] = {}
for _idx, _cls in enumerate(_ARABIC_EQUIVALENCE_CLASSES):
    for _ch in _cls:
        _CHAR_TO_CLASSES.setdefault(_ch, set()).add(_idx)


def _substitution_cost(a: str, b: str) -> float:
    if a == b:
        return 0.0
    classes_a = _CHAR_TO_CLASSES.get(a)
    classes_b = _CHAR_TO_CLASSES.get(b)
    if classes_a and classes_b and classes_a & classes_b:
        return _SIMILAR_COST
    return 1.0


def levenshtein(a: str, b: str, has_equivalence_sub_cost: bool = False) -> float:
    """Calculate the Levenshtein distance between two strings.

    Characters in the same equivalence class (ALEFAT, HAMZAT, TEHLIKE,
    WAWLIKE, YEHLIKE, WEAK) incur a lower substitution cost than 1.0.

    Args:
        a: First Arabic string (unvocalized).
        b: Second Arabic string (unvocalized).
        has_equivalence_sub_cost: Whether to use equivalence class substitution costs.

    Returns:
        Float edit distance.
    """
    n = len(a)
    m = len(b)

    if n == 0:
        return m
    if m == 0:
        return n

    dp = [[0.0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i

    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = (
                1.0
                if not has_equivalence_sub_cost
                else _substitution_cost(a[i - 1], b[j - 1])
            )
            dp[i][j] = min(
                dp[i - 1][j] + 1.0,
                dp[i][j - 1] + 1.0,
                dp[i - 1][j - 1] + cost,
            )

            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]

    return dp[n][m]
