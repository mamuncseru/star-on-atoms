"""Protocol P02's registered analysis, in one place.

H2 (the shape): for each distance and each full-grid model, the injection
errors divided by starlab.branch_flip_shape agree to within a factor 1.5
over the points with at least 100 errors (at least four of the six).
E1 and E2 are reported ratios with registered expectations, not verdicts.

Run:  python tools/analyze_p02.py      (re-reads the committed artifact)
"""

from __future__ import annotations

import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARTIFACT = ROOT / "data" / "results" / "p02_injection_error.json"

MIN_ERRORS, MIN_POINTS, MAX_SPREAD = 100, 4, 1.5


def grid(points, d, model):
    return sorted((p for p in points if p["d"] == d and p["model"] == model
                   and p["role"] == "grid"), key=lambda p: p["n"])


def fit(points):
    """A, the one free constant: errors / sum(accepted * f)."""
    return (sum(p["logical_errors"] for p in points)
            / sum(p["shots"] * p["shape"] for p in points))


def shape_test(points, d, model) -> dict:
    usable = [p for p in grid(points, d, model)
              if p["logical_errors"] >= MIN_ERRORS]
    ratios = [p["logical_error_rate"] / p["shape"] for p in usable]
    if len(usable) < MIN_POINTS:
        verdict, spread = "UNDERPOWERED", None
    else:
        spread = max(ratios) / min(ratios)
        verdict = "PASS" if spread <= MAX_SPREAD else "FAIL"
    return {"d": d, "model": model, "usable_n": [p["n"] for p in usable],
            "rate_over_shape": ratios, "spread": spread,
            "A": fit(usable) if usable else None, "verdict": verdict}


def ratio(a, b) -> dict:
    """a's rate over b's, with a 95% Katz log interval."""
    r = a["logical_error_rate"] / b["logical_error_rate"]
    se = math.sqrt(1 / a["logical_errors"] - 1 / a["shots"]
                   + 1 / b["logical_errors"] - 1 / b["shots"])
    return {"ratio": r, "ci95": [r * math.exp(-1.96 * se),
                                 r * math.exp(1.96 * se)]}


def analyse(points, models, distances) -> dict:
    shapes = [shape_test(points, d, m) for d in distances
              for m in ("U", "T")]
    verdicts = {s["verdict"] for s in shapes}
    h2 = ("REFUTED" if "FAIL" in verdicts else
          "UNDERPOWERED" if "UNDERPOWERED" in verdicts else "CONFIRMED")
    e1 = {str(d): next(s["A"] for s in shapes if s["d"] == d
                       and s["model"] == "T")
          / next(s["A"] for s in shapes if s["d"] == d and s["model"] == "U")
          for d in distances}
    e2 = []
    for d in distances:
        base = next(p for p in grid(points, d, "T") if p["n"] == 4)
        for m in models:
            for p in points:
                if p["d"] == d and p["model"] == m and p["role"] == "variant":
                    e2.append({"d": d, "variant": m, **ratio(p, base),
                               "acceptance_ratio": p["acceptance"]
                               / base["acceptance"]})
    return {"H2_shape": {"verdict": h2, "per_pair": shapes},
            "E1_A_T_over_A_U": e1, "E2_variants_vs_T": e2}


def main() -> int:
    record = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    print(json.dumps(record["analysis"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
