"""Diagnose a P01 shape failure, as the protocol prescribes.

P01's "fail in shape" branch registers two diagnostics, run here first:

  R1  post-select on *all* detectors: a lower bound that needs no decoder
  R2  count decomposition failures in the decoder's error model

and then, clearly labelled EXPLORATORY because the protocol did not
register them, one hypothesis test:

  X1  how the decoded floor moves if fewer injection rounds are
      post-selected (0, 1, 2 or the registered 3). If the reference plot
      was made with a weaker post-selection window, its floor would sit
      above this book's at d = 3 and much less so at d = 5, which is the
      pattern P01 found.

Writes data/results/p01_diagnosis.json.

Run:  python tools/diagnose_p01.py
"""

from __future__ import annotations

import datetime
import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from starlab import star_circuit                         # noqa: E402
from starlab.sampling import matcher                     # noqa: E402
from starlab.stats import rate_record                    # noqa: E402

sys.path.insert(0, str(ROOT / "tools"))
from measure_p01 import environment                      # noqa: E402

THETAS = (1e-4, 0.1)
SHOTS = {3: 1_000_000, 5: 2_000_000}
SEED = 20261027


def run(d: int, theta: float) -> dict:
    circuit = star_circuit(d, theta)
    per_round = d * d - 1
    dem = circuit.stim_circuit.detector_error_model(
        decompose_errors=True, ignore_decomposition_failures=True)
    strict = circuit.stim_circuit.detector_error_model(decompose_errors=True)
    decoder = matcher(circuit)
    sampler = circuit.compile_detector_sampler(seed=SEED + d)
    dets, obs = sampler.sample(SHOTS[d], separate_observables=True)
    dets, obs = np.asarray(dets, bool), np.asarray(obs, bool)

    out = {"d": d, "theta_rad": theta, "shots_sampled": SHOTS[d],
           "seed": SEED + d,
           "R2_dem_errors": dem.num_errors,
           "R2_decomposition_failures": dem.num_errors - strict.num_errors}

    every = ~dets.any(axis=1)
    out["R1_all_detectors_postselected"] = rate_record(
        int(obs[every, 0].sum()), int(every.sum()))
    out["R1_all_detectors_postselected"]["acceptance"] = float(every.mean())

    window = {}
    for rounds in (0, 1, 2, 3):
        keep = ~dets[:, :rounds * per_round].any(axis=1) if rounds else \
            np.ones(len(dets), bool)
        predicted = decoder.decode_batch(dets[keep]).astype(bool)
        errors = int((predicted[:, 0] != obs[keep, 0]).sum())
        record = rate_record(errors, int(keep.sum()))
        record["acceptance"] = float(keep.mean())
        record["per_distance"] = record["logical_error_rate"] / d
        window[f"{rounds}_rounds"] = record
    out["X1_postselection_window_EXPLORATORY"] = window
    return out


def main() -> int:
    points = []
    for d in sorted(SHOTS):
        for theta in THETAS:
            point = run(d, theta)
            points.append(point)
            w = point["X1_postselection_window_EXPLORATORY"]
            print(f"d={d} θ={theta:g}  R1 all-detector rate="
                  f"{point['R1_all_detectors_postselected']['logical_error_rate']:.2e}"
                  f"  R2 failures={point['R2_decomposition_failures']}  "
                  + "  ".join(f"{k}: {v['per_distance']:.2e}"
                              for k, v in w.items()), flush=True)
    record = {"protocol": "P01 (diagnosis)",
              "captured": datetime.date.today().isoformat(),
              "seed_base": SEED, "environment": environment(),
              "points": points}
    out = ROOT / "data" / "results" / "p01_diagnosis.json"
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
