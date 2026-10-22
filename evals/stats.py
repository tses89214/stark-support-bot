"""Shared by the evals."""


def wilson(k, n, z=1.96):
    """95% Wilson interval for k successes in n trials."""
    if n == 0:
        return 0.0, 1.0

    p, d = k / n, 1 + z * z / n
    mid, half = (p + z * z / (2 * n)) / d, z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / d
    return mid - half, mid + half
