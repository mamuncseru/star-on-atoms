"""Intervals for rare events.

A logical error rate below threshold is a count of rare failures, and a
rate printed without its interval is not a result. The Wilson score
interval is the one used throughout, because it stays inside [0, 1] and
behaves at zero observed failures, where the textbook normal interval
collapses to a point.
"""

from __future__ import annotations

import math


def wilson(successes: int, trials: int, z: float = 1.959964) -> tuple:
    """95% Wilson score interval for a binomial proportion."""
    if trials <= 0:
        return (0.0, 1.0)
    p = successes / trials
    denom = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denom
    half = z * math.sqrt(p * (1 - p) / trials
                         + z * z / (4 * trials * trials)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def rate_record(errors: int, shots: int) -> dict:
    """The fields tools/check_results.py demands of every measured rate."""
    lo, hi = wilson(errors, shots)
    return {"shots": int(shots), "logical_errors": int(errors),
            "logical_error_rate": errors / shots if shots else 0.0,
            "wilson_95": [lo, hi]}
