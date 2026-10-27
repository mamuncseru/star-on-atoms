"""Run P01's diagnostic R6: the "naive pipeline".

Executes exactly what P01's Deviations entry "R6 registered" specifies:
fresh samples on the registered P01 grid, every accepted shot decoded by
matching on the Clifford proxy (this book's decoder) and by matching on
tsim's default, undecomposed detector error model (which PyMatching builds
from its graph-like mechanisms only). The verdict applies P01's own
registered criterion to the naive pipeline, via tools/analyze_p01.py.

Writes data/results/p01_r6_naive_pipeline.json.

Run:  python tools/diagnose_p01_r6.py
"""

from __future__ import annotations

import datetime
import json
import math
import pathlib
import sys
import time

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from analyze_p01 import verdict                          # noqa: E402
from measure_p01 import THETAS, environment              # noqa: E402
from starlab import n_postselected, star_circuit         # noqa: E402
from starlab.sampling import matcher                     # noqa: E402
from starlab.stats import rate_record                    # noqa: E402

SHOTS = {3: 1_000_000, 5: 2_000_000}
REFERENCE = json.loads((ROOT / "data" / "reference"
                        / "eth_qhack_2026_star_sim.json").read_text())


def naive_matcher(circuit):
    import pymatching

    return pymatching.Matching.from_detector_error_model(
        circuit.detector_error_model())


def run_point(d: int, i: int, theta: float) -> dict:
    circuit = star_circuit(d, theta)
    seed = 20261029 + 1000 * d + i
    dets, obs = circuit.compile_detector_sampler(seed=seed).sample(
        SHOTS[d], separate_observables=True)
    dets, obs = np.asarray(dets, bool), np.asarray(obs, bool)
    keep = ~dets[:, :n_postselected(d)].any(axis=1)
    dets, obs = dets[keep], obs[keep, 0]
    ref = REFERENCE["curves"][f"d={d}"][i]["logical_error_per_distance"]
    out = {"d": d, "theta_rad": theta, "seed": seed,
           "shots_sampled": SHOTS[d], "acceptance": float(keep.mean()),
           "reference_per_distance": ref}
    for name, build in (("proxy_matching", matcher),
                        ("naive_matching", naive_matcher)):
        pred = build(circuit).decode_batch(dets).astype(bool)[:, 0]
        rec = rate_record(int((pred != obs).sum()), int(keep.sum()))
        rec["per_distance"] = rec["logical_error_rate"] / d
        out[name] = rec
    return out


def main() -> int:
    points = []
    for d in sorted(SHOTS):
        for i, theta in enumerate(THETAS):
            start = time.time()
            p = run_point(d, i, theta)
            points.append(p)
            print(f"d={d} θ={theta:.2e} acc={p['acceptance']:.3f}  proxy "
                  f"{p['proxy_matching']['per_distance']:.2e}  naive "
                  f"{p['naive_matching']['per_distance']:.2e}  ref "
                  f"{p['reference_per_distance']:.2e}  "
                  f"[{time.time() - start:.0f}s]", flush=True)

    naive = [{"d": p["d"], "theta_rad": p["theta_rad"],
              "logical_errors": p["naive_matching"]["logical_errors"],
              "wilson_95": p["naive_matching"]["wilson_95"],
              "per_distance": p["naive_matching"]["per_distance"],
              "reference_per_distance": p["reference_per_distance"]}
             for p in points]
    result = verdict(naive)
    print(f"\nnaive pipeline under P01's registered criterion: "
          f"geometric mean {result['geometric_mean']:.3f}, range "
          f"{min(result['ratios']):.2f}-{max(result['ratios']):.2f} -> "
          f"{result['outcome']}")

    record = {"protocol": "P01 (diagnosis R6, registered 2026-10-27)",
              "captured": datetime.date.today().isoformat(),
              "seed_base": 20261029, "environment": environment(),
              "points": points,
              "naive_pipeline_verdict": {
                  "geometric_mean": result["geometric_mean"],
                  "ratio_min": min(result["ratios"]),
                  "ratio_max": max(result["ratios"]),
                  "outcome": result["outcome"]}}
    out = ROOT / "data" / "results" / "p01_r6_naive_pipeline.json"
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
