"""Run P01's diagnostics R3, R4 and the yardstick R5.

Executes exactly what P01's Deviations entry of 2026-10-27 registers:

  R3  paired decoding of the same accepted shots by matching (Clifford
      proxy) and by bloqade's BpLsdDecoder on tsim's undecomposed DEM
  R4  the Clifford proxy sampled by stim instead of tsim, decoded by
      matching, at theta = 1e-4
  R5  stim's standard rotated-surface-code X-memory at p = 1e-3 (reported
      only; a different circuit)

Writes data/results/p01_diagnosis_r3_r5.json.

Run:  python tools/diagnose_p01b.py
"""

from __future__ import annotations

import datetime
import json
import multiprocessing as mp
import pathlib
import sys
import time

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from measure_p01 import environment                      # noqa: E402
from starlab import n_postselected, star_circuit         # noqa: E402
from starlab.sampling import matcher                     # noqa: E402
from starlab.stats import rate_record                    # noqa: E402

SHOTS = {3: 1_000_000, 5: 2_000_000}
THETAS = (1e-4, 0.1)
WORKERS = 32
REFERENCE = json.loads((ROOT / "data" / "reference"
                        / "eth_qhack_2026_star_sim.json").read_text())


def seed_for(d: int, theta: float) -> int:
    return 20261028 + d + (100 if theta > 1e-3 else 0)


def _bplsd_chunk(args):
    d, theta, chunk = args
    from bloqade.decoders import BpLsdDecoder
    dem = star_circuit(d, theta).detector_error_model()
    return np.asarray(BpLsdDecoder(dem).decode(chunk), dtype=bool)


def bplsd(d, theta, dets):
    chunks = np.array_split(dets, WORKERS)
    with mp.get_context("spawn").Pool(WORKERS) as pool:
        parts = pool.map(_bplsd_chunk, [(d, theta, c) for c in chunks])
    return np.concatenate(parts)


def reference_at(d: int, theta: float) -> float:
    curve = REFERENCE["curves"][f"d={d}"]
    return min(curve, key=lambda p: abs(np.log(p["theta_rad"] / theta))
               )["logical_error_per_distance"]


def r3(d: int, theta: float) -> dict:
    circuit = star_circuit(d, theta)
    seed = seed_for(d, theta)
    sampler = circuit.compile_detector_sampler(seed=seed)
    dets, obs = sampler.sample(SHOTS[d], separate_observables=True)
    dets, obs = np.asarray(dets, bool), np.asarray(obs, bool)
    keep = ~dets[:, :n_postselected(d)].any(axis=1)
    dets, obs = dets[keep], obs[keep, 0]

    start = time.time()
    mwpm = matcher(circuit).decode_batch(dets).astype(bool)[:, 0]
    t_mwpm = time.time() - start
    start = time.time()
    bp = bplsd(d, theta, dets)[:, 0]
    t_bp = time.time() - start

    out = {"d": d, "theta_rad": theta, "seed": seed,
           "shots_sampled": SHOTS[d], "acceptance": float(keep.mean()),
           "reference_per_distance": reference_at(d, theta)}
    for name, pred, secs in (("matching", mwpm, t_mwpm),
                             ("bp_lsd", bp, t_bp)):
        rec = rate_record(int((pred != obs).sum()), int(keep.sum()))
        rec["per_distance"] = rec["logical_error_rate"] / d
        rec["ratio_to_reference"] = (rec["per_distance"]
                                     / out["reference_per_distance"])
        rec["decode_seconds"] = round(secs, 1)
        out[name] = rec
    out["disagreements"] = int((mwpm != bp).sum())
    return out


def r4(d: int) -> dict:
    theta = 1e-4
    circuit = star_circuit(d, theta)
    seed = seed_for(d, theta)
    sampler = circuit.stim_circuit.compile_detector_sampler(seed=seed)
    dets, obs = sampler.sample(SHOTS[d], separate_observables=True)
    keep = ~dets[:, :n_postselected(d)].any(axis=1)
    pred = matcher(circuit).decode_batch(dets[keep]).astype(bool)[:, 0]
    rec = rate_record(int((pred != obs[keep, 0]).sum()), int(keep.sum()))
    rec.update({"d": d, "theta_rad": theta, "seed": seed,
                "sampler": "stim (Clifford proxy)",
                "acceptance": float(keep.mean()),
                "per_distance": rec["logical_error_rate"] / d})
    return rec


def r5(d: int, p: float = 1e-3, shots: int = 1_000_000) -> dict:
    import pymatching
    import stim

    circ = stim.Circuit.generated(
        "surface_code:rotated_memory_x", distance=d, rounds=d,
        after_clifford_depolarization=p, after_reset_flip_probability=p,
        before_measure_flip_probability=p,
        before_round_data_depolarization=p)
    m = pymatching.Matching.from_detector_error_model(
        circ.detector_error_model(decompose_errors=True))
    dets, obs = circ.compile_detector_sampler(seed=20261028).sample(
        shots, separate_observables=True)
    fails = int((m.decode_batch(dets)[:, 0] != obs[:, 0]).sum())
    rec = rate_record(fails, shots)
    rec.update({"d": d, "p": p, "rounds": d, "seed": 20261028,
                "circuit": "stim generated rotated_memory_x",
                "per_distance": rec["logical_error_rate"] / d})
    return rec


def main() -> int:
    record = {"protocol": "P01 (diagnosis R3-R5, registered 2026-10-27)",
              "captured": datetime.date.today().isoformat(),
              "seed_base": 20261028, "environment": environment(),
              "R3": [], "R4": [], "R5": []}
    for d in sorted(SHOTS):
        for theta in THETAS:
            point = r3(d, theta)
            record["R3"].append(point)
            print(f"R3 d={d} θ={theta:g} acc={point['acceptance']:.3f}  "
                  f"matching {point['matching']['per_distance']:.2e} "
                  f"({point['matching']['logical_errors']})  "
                  f"BP-LSD {point['bp_lsd']['per_distance']:.2e} "
                  f"({point['bp_lsd']['logical_errors']})  "
                  f"ref {point['reference_per_distance']:.2e}  "
                  f"[{point['bp_lsd']['decode_seconds']}s]", flush=True)
        point = r4(d)
        record["R4"].append(point)
        print(f"R4 d={d} stim-sampled floor {point['per_distance']:.2e} "
              f"({point['logical_errors']})", flush=True)
        point = r5(d)
        record["R5"].append(point)
        print(f"R5 d={d} textbook memory {point['per_distance']:.2e} "
              f"per distance ({point['logical_errors']})", flush=True)
    out = ROOT / "data" / "results" / "p01_diagnosis_r3_r5.json"
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
