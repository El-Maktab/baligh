"""String distance and similarity utilities."""


def levenshtein(a: str, b: str) -> int:
    """Calculate the Levenshtein distance between two strings."""
    n = len(a)
    m = len(b)

    if n == 0:
        return m
    if m == 0:
        return n

    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i

    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]

    return dp[n][m]
