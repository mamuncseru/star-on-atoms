"""Run Protocol P03: the exact first-order injection error against P02.

Executes what protocols/P03-exact-first-order.md registers. For every
circuit P02 sampled (same builder, same angles, same variants),
`starlab.enumerate` predicts the injection error with no free parameter;
the prediction is compared with P02's committed counts under the registered
rule. Also reports the census, the share of the weight at m = 1, a
chi-square over the 32 grid points, and first-order additivity over
Table II rows.

Writes data/results/p03_exact_vs_p02.json. Run:
    nice -n 19 python tools/measure_p03.py
"""

from __future__ import annotations

import datetime
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from measure_p01 import environment                       # noqa: E402
from measure_p02 import build                             # noqa: E402
from starlab import branch_flip_shape, star_text          # noqa: E402
from starlab import renoise as rn                         # noqa: E402
from starlab.enumerate import injection_error, matches    # noqa: E402

P02 = ROOT / "data" / "results" / "p02_injection_error.json"
CONFIRM, REFUTE = (0.92, 1.08), (0.85, 1.18)
OPTIONS = {"T-naiveH": {"hadamards": "naive"},
           "T-datamove": {"mover": "data"}}


def predict(d: int, model: str, n: int) -> dict:
    theta = math.pi / 2 ** n
    clean = rn.renoise(star_text(d, theta), d, (), **OPTIONS.get(model, {}))
    found, census = matches(build(d, model, n), clean)
    by_m = {}
    for f in found:
        by_m[f.m] = by_m.get(f.m, 0.0) + f.p
    rate = injection_error(found, theta, d)
    m1 = injection_error([f for f in found if f.m == 1], theta, d)
    return {"rate": rate, "share_m1": m1 / rate if rate else None,
            "p_by_m": {str(m): p for m, p in sorted(by_m.items())},
            "census": census}


def additivity(d: int, n: int = 4) -> dict:
    """First-order sum over Table II rows, one DEM per row, vs all-on."""
    theta = math.pi / 2 ** n
    clean = rn.renoise(star_text(d, theta), d, ())
    full = rn.table_ii(1e-3)

    def rate(model):
        text = rn.renoise(star_text(d, theta), d, model, window="injection")
        return injection_error(matches(text, clean)[0], theta, d)

    rows = sorted({row for row, _, _ in full})
    per_row = {row: rate(rn.only(full, row)) for row in rows}
    total = rate(full)
    return {"theta_rad": theta, "per_row": per_row, "all_on": total,
            "sum_over_all_on": sum(per_row.values()) / total}


def main() -> int:
    from scipy.stats import chi2
    p02 = json.loads(P02.read_text(encoding="utf-8"))
    points = []
    for p in p02["points"]:
        pred = predict(p["d"], p["model"], p["n"])
        expected = pred["rate"] * p["shots"]
        points.append({"d": p["d"], "model": p["model"], "n": p["n"],
                       "role": p["role"], "theta_rad": p["theta_rad"],
                       "p02_errors": p["logical_errors"],
                       "p02_accepted": p["shots"],
                       "p02_rate": p["logical_error_rate"],
                       "p02_wilson_95": p["wilson_95"],
                       "predicted_rate": pred["rate"],
                       "predicted_errors": expected,
                       "share_m1": pred["share_m1"],
                       "p_by_m": pred["p_by_m"], "census": pred["census"]})
        print(f"d={p['d']} {p['model']:<11} n={p['n']}  P02 "
              f"{p['logical_error_rate']:.3e}  C {pred['rate']:.3e}  "
              f"ratio {pred['rate'] / p['logical_error_rate']:.3f}",
              flush=True)

    pairs = []
    for d in (3, 5):
        for model in ("U", "T"):
            g = [q for q in points if q["d"] == d and q["model"] == model
                 and q["role"] == "grid"]
            shape = [branch_flip_shape(q["theta_rad"], d) for q in g]
            a_p02 = (sum(q["p02_errors"] for q in g)
                     / sum(q["p02_accepted"] * f for q, f in zip(g, shape)))
            a_c = (sum(q["predicted_rate"] * q["p02_accepted"] for q in g)
                   / sum(q["p02_accepted"] * f for q, f in zip(g, shape)))
            pairs.append({"d": d, "model": model, "A_P02_over_p": a_p02 / 1e-3,
                          "A_C_over_p": a_c / 1e-3, "ratio": a_c / a_p02})
    variants = []
    ana = p02["analysis"]["E2_variants_vs_T"]
    for e in ana:
        base = next(q for q in points if q["d"] == e["d"]
                    and q["model"] == "T" and q["n"] == 4)
        var = next(q for q in points if q["d"] == e["d"]
                   and q["model"] == e["variant"])
        ratio = var["predicted_rate"] / base["predicted_rate"]
        lo, hi = e["ci95"]
        variants.append({"d": e["d"], "variant": e["variant"],
                         "predicted_ratio": ratio, "p02_ratio": e["ratio"],
                         "p02_ci95": e["ci95"], "inside": lo <= ratio <= hi})
    grid = [q for q in points if q["role"] == "grid"]
    stat = sum((q["p02_errors"] - q["predicted_errors"]) ** 2
               / q["predicted_errors"] for q in grid)
    p_value = float(chi2.sf(stat, len(grid)))
    ratios = [r["ratio"] for r in pairs]
    inside = sum(v["inside"] for v in variants)
    if any(not REFUTE[0] <= r <= REFUTE[1] for r in ratios):
        verdict = "REFUTED"
    elif all(CONFIRM[0] <= r <= CONFIRM[1] for r in ratios) and inside >= 7:
        verdict = "CONFIRMED"
    else:
        verdict = "INCONCLUSIVE"
    weights = [q["share_m1"] for q in points if q["share_m1"] is not None]
    summary = {"verdict": verdict, "pairs": pairs,
               "variants_inside": f"{inside}/8", "variants": variants,
               "chi2": stat, "chi2_dof": len(grid), "chi2_p": p_value,
               "min_share_m1": min(weights),
               "additivity": [additivity(d) for d in (3, 5)]}
    record = {"protocol": "P03", "captured": datetime.date.today().isoformat(),
              "seed": "none: deterministic enumeration",
              "environment": environment(), "points": points,
              "summary": summary}
    out = ROOT / "data" / "results" / "p03_exact_vs_p02.json"
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items()
                      if k not in ("variants",)}, indent=2))
    print("variants:", [(v["d"], v["variant"],
                         round(v["predicted_ratio"], 3), v["inside"])
                        for v in variants])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
