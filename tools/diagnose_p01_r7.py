"""Run P01's diagnostic R7: is the angle-dependent regime a read-out artifact?

Executes exactly what P01's Deviations entry "R7 registered" specifies:
three noise windows (all, memory, injection) on the published circuits,
P01's post-selection and proxy decoder, and the registered reading rule.

Writes data/results/p01_r7_readout_artifact.json.

Run:  python tools/diagnose_p01_r7.py
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

import tsim                                              # noqa: E402

from measure_p01 import environment                      # noqa: E402
from starlab.circuits import restrict_noise, star_text   # noqa: E402
from starlab.sampling import sample_star                 # noqa: E402

SHOTS = {3: 1_000_000, 5: 2_000_000}
THETAS = (1e-4, 0.1, 0.398, math.pi / 4)
WINDOWS = ("all", "memory", "injection")


def excess(points, window, theta):
    rate = {p["theta_rad"]: p["logical_error_rate"] for p in points
            if p["window"] == window}
    return rate[theta] - rate[THETAS[0]]


def judge(points, d):
    mine = [p for p in points if p["d"] == d]
    per_sin2 = [excess(mine, "memory", t) / math.sin(t) ** 2
                for t in THETAS[1:]]
    spread = max(per_sin2) / min(per_sin2) if min(per_sin2) > 0 else math.inf
    share = {t: excess(mine, "memory", t) / excess(mine, "all", t)
             for t in THETAS[2:]}
    additivity = {t: (excess(mine, "memory", t)
                      + excess(mine, "injection", t)) / excess(mine, "all", t)
                  for t in THETAS[1:]}
    confirmed = spread <= 1.5 and all(s >= 0.5 for s in share.values())
    return {"d": d, "memory_excess_per_sin2": per_sin2,
            "memory_excess_per_sin2_spread": spread,
            "memory_share_of_all_excess": {str(t): s
                                           for t, s in share.items()},
            "additivity_reported": {str(t): a
                                    for t, a in additivity.items()},
            "artifact_confirmed": confirmed}


def main() -> int:
    points = []
    for d in sorted(SHOTS):
        for v, window in enumerate(WINDOWS):
            for i, theta in enumerate(THETAS):
                text = restrict_noise(star_text(d, theta), d, window)
                seed = 20261030 + 1000 * d + 10 * v + i
                rec = sample_star(d, theta, SHOTS[d], seed,
                                  circuit=tsim.Circuit(text))
                rec["window"] = window
                points.append(rec)
                print(f"d={d} {window:<9} θ={theta:.3e}  "
                      f"acc={rec['acceptance']:.3f}  "
                      f"rate={rec['logical_error_rate']:.3e} "
                      f"({rec['logical_errors']})", flush=True)
    verdicts = [judge(points, d) for d in sorted(SHOTS)]
    for v in verdicts:
        print(f"\nd={v['d']}: memory excess / sin^2 = "
              + ", ".join(f"{x:.2e}" for x in v["memory_excess_per_sin2"])
              + f"  (spread {v['memory_excess_per_sin2_spread']:.2f})")
        print("  memory share of all-noise excess: "
              + ", ".join(f"θ={k[:5]}: {s:.2f}" for k, s in
                          v["memory_share_of_all_excess"].items()))
        print("  additivity (reported): "
              + ", ".join(f"θ={k[:5]}: {a:.2f}" for k, a in
                          v["additivity_reported"].items()))
        print(f"  artifact confirmed: {v['artifact_confirmed']}")
    record = {"protocol": "P01 (diagnosis R7, registered 2026-10-27)",
              "captured": datetime.date.today().isoformat(),
              "seed_base": 20261030, "environment": environment(),
              "points": points, "verdicts": verdicts}
    out = ROOT / "data" / "results" / "p01_r7_readout_artifact.json"
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
