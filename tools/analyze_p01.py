"""Apply Protocol P01's registered criteria to its artifacts.

The verdict is computed, not judged: this script reads the committed P01
artifacts and applies exactly the criteria written in
protocols/P01-reproduce-uniform-star.md before the run —

  primary   geometric mean of r_i in [0.80, 1.25], and every r_i in
            [0.5, 2.0], over the 16 points (d = 3, 5 x 8 angles), where
            r_i = (this book's rate / d) / (digitized reference value)
  common    "fail by a common factor" if every r_i is within ±20% of one
            constant c outside [0.80, 1.25]; otherwise "fail in shape"
  power     a point with fewer than 30 logical errors is underpowered

Run:  python tools/analyze_p01.py
"""

from __future__ import annotations

import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "data" / "results"


def load() -> list[dict]:
    points = []
    for d in (3, 5):
        record = json.loads((RESULTS / f"p01_uniform_star_d{d}.json")
                            .read_text())
        points.extend(record["points"])
    return points


def verdict(points: list[dict]) -> dict:
    ratios = [p["per_distance"] / p["reference_per_distance"]
              for p in points]
    gmean = math.exp(sum(math.log(r) for r in ratios) / len(ratios))
    primary = (0.80 <= gmean <= 1.25
               and all(0.5 <= r <= 2.0 for r in ratios))
    common = all(abs(r / gmean - 1) <= 0.20 for r in ratios)
    under = [(p["d"], p["theta_rad"]) for p in points
             if p["logical_errors"] < 30]
    contained = sum(p["wilson_95"][0] / p["d"]
                    <= p["reference_per_distance"]
                    <= p["wilson_95"][1] / p["d"] for p in points)
    if primary:
        outcome = "PASS"
    elif common:
        outcome = "FAIL by a common factor"
    else:
        outcome = "FAIL in shape"
    return {"ratios": ratios, "geometric_mean": gmean, "outcome": outcome,
            "underpowered": under, "reference_inside_interval": contained}


def main() -> int:
    points = load()
    result = verdict(points)
    print(f"{'d':>2}{'theta':>10}{'acc':>8}{'ideal':>8}{'errors':>8}"
          f"{'rate/d':>11}{'reference':>11}{'ratio':>8}")
    for p, r in zip(points, result["ratios"]):
        print(f"{p['d']:>2}{p['theta_rad']:>10.2e}{p['acceptance']:>8.3f}"
              f"{p['ideal_acceptance']:>8.3f}{p['logical_errors']:>8}"
              f"{p['per_distance']:>11.2e}"
              f"{p['reference_per_distance']:>11.2e}{r:>8.2f}")
    print()
    print(f"geometric mean ratio   {result['geometric_mean']:.3f}  "
          f"(registered window 0.80-1.25)")
    print(f"ratio range            {min(result['ratios']):.2f}-"
          f"{max(result['ratios']):.2f}  (registered window 0.5-2.0)")
    print(f"reference inside 95%   {result['reference_inside_interval']}"
          f" of {len(points)}  (reported, not pass/fail)")
    print(f"underpowered points    {result['underpowered'] or 'none'}")
    print(f"P01 outcome            {result['outcome']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
