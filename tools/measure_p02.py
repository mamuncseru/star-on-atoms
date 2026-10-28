"""Run Protocol P02: re-noise STAR with Table II, measure the injection error.

Executes exactly what protocols/P02-renoise-table-ii.md registers:

1. The deterministic checks V1 (uniform re-noise reproduces the published
   error model) and V3 (accounting, Hadamard counts) -> p02_validation.json.
   V2 is the test suite (tests/test_starlab.py), run here first.
2. The injection error under models U (uniform) and T (Table II at
   p_ph = 1e-3) on the full angle grid, and four variants of T at pi/16,
   noise in the injection window only, every detector post-selected.
   -> p02_injection_error.json, with the registered analysis.

Points run in fixed-size chunks with seeds fixed by the protocol. A point
stops at the first chunk where its errors reach 400 (or at the cap); chunks
computed beyond that by the parallel scheduler are discarded, so the result
does not depend on scheduling.

Run:  taskset -c 0-31 python tools/measure_p02.py
"""

from __future__ import annotations

import datetime
import json
import math
import multiprocessing as mp
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

DISTANCES = (3, 5)
GRID_N = (2, 3, 4, 5, 6, 7)                      # theta = pi / 2^n
VARIANT_N = 4
CHUNK = {3: 1_000_000, 5: 2_000_000}
CAP = {3: 40_000_000, 5: 100_000_000}
TARGET_ERRORS = 400
WORKERS = 10
CEILING_S = 2.5 * 3600
# Model index m enters the seed: seed = 1e6 d + 1e4 m + 100 n + chunk.
MODELS = ("U", "T", "T-naiveH", "T-datamove", "T-pairloss", "T-ffnoise")


def build(d: int, model: str, n: int) -> str:
    from starlab import renoise as rn
    from starlab import star_text
    p = 1e-3
    noise = {"U": rn.uniform(p),
             "T-pairloss": rn.table_ii(p, loss_on_spectators=False),
             "T-ffnoise": rn.table_ii(p, feedforward_noise=True)}.get(
                 model, rn.table_ii(p))
    options = {"T-naiveH": {"hadamards": "naive"},
               "T-datamove": {"mover": "data"}}.get(model, {})
    return rn.renoise(star_text(d, math.pi / 2 ** n), d, noise,
                      window="injection", **options)


def seed(d: int, model: str, n: int, chunk: int) -> int:
    return 1_000_000 * d + 10_000 * MODELS.index(model) + 100 * n + chunk


def run_chunk(task):
    d, model, n, chunk, shots = task
    import tsim
    from starlab.sampling import sample_injection
    rec = sample_injection(tsim.Circuit(build(d, model, n)), shots,
                           seed(d, model, n, chunk))
    return task, rec["logical_errors"], rec["shots"]


def validation() -> dict:
    """V1 and V3; V2 is the test suite, which must pass first."""
    import tsim
    from starlab import renoise as rn
    from starlab.circuits import n_postselected, source

    tests = subprocess.run([sys.executable, str(ROOT / "tests" /
                                                "test_starlab.py")],
                           capture_output=True, text=True)
    if tests.returncode != 0:
        print(tests.stdout, tests.stderr)
        raise SystemExit("V2: the test suite fails; P02 stops here")

    def symptoms(text):
        out = {}
        dem = tsim.Circuit(text).stim_circuit.detector_error_model()
        for inst in dem.flattened():
            if inst.type == "error":
                key = tuple(sorted(str(t) for t in inst.targets_copy()))
                p, q = out.get(key, 0.0), inst.args_copy()[0]
                out[key] = p * (1 - q) + q * (1 - p)
        return out

    def gap(a, b):
        return max(abs(a.get(k, 0.0) - b.get(k, 0.0))
                   for k in set(a) | set(b))

    v1 = []
    for d in (3, 5, 7):
        published = symptoms(source(d))
        for hadamards in ("minimal", "naive"):
            for mover in ("ancilla", "data"):
                text = rn.renoise(source(d), d, rn.uniform(1e-3),
                                  hadamards=hadamards, mover=mover)
                v1.append({"d": d, "hadamards": hadamards, "mover": mover,
                           "symptoms": len(published),
                           "max_abs_gap": gap(symptoms(text), published)})
    controls = {role: gap(symptoms(rn.renoise(
        source(3), 3, tuple(e for e in rn.uniform(1e-3) if e[1] != role))),
        symptoms(source(3)))
        for role in ("init", "spectator", "feedforward", "idle1",
                     "measure")}
    v1_pass = (all(r["max_abs_gap"] < 1e-15 for r in v1)
               and all(g > 1e-4 for g in controls.values()))
    counts = {}
    for d in DISTANCES:
        for hadamards in ("minimal", "naive"):
            text = rn.renoise(source(d), d, rn.table_ii(1e-3),
                              hadamards=hadamards)
            counts[f"d={d} {hadamards}"] = {
                "injection_window": rn.hadamard_count(
                    text, window_detectors=n_postselected(d)),
                "all_noisy_rounds": rn.hadamard_count(text)}
    return {"V1_pass": v1_pass, "V1": v1, "V1_negative_controls": controls,
            "V2_pass": True,
            "V3": {"p_ph_table_ii": rn.combined(rn.table_ii()),
                   "p_ph_operating_point": rn.combined(rn.table_ii(1e-3)),
                   "scale": 1e-3 / rn.combined(rn.table_ii()),
                   "p_cz": sum(rn.CZ_PAULI),
                   "hadamards": counts}}


def tasks_for(points):
    """(d, model, n, role) for every registered point."""
    for d in DISTANCES:
        for model in ("U", "T"):
            for n in GRID_N:
                points.append((d, model, n, "grid"))
        for model in MODELS[2:]:
            points.append((d, model, VARIANT_N, "variant"))
    return points


def measure() -> list[dict]:
    points = tasks_for([])
    state = {p[:3]: {"done": {}, "next": 0, "stopped": None}
             for p in points}
    start = time.time()
    with mp.get_context("spawn").Pool(WORKERS) as pool:
        pending = set()

        def submit(key):
            task = (*key, state[key]["next"], CHUNK[key[0]])
            state[key]["next"] += 1
            pending.add(pool.apply_async(run_chunk, (task,)))

        def settle(key):
            # Walk the contiguous prefix of finished chunks; stop at the
            # first chunk where errors reach the target, or at the cap.
            s, errors, c = state[key], 0, 0
            while c in s["done"] and s["stopped"] is None:
                errors += s["done"][c][0]
                if errors >= TARGET_ERRORS:
                    s["stopped"] = ("errors", c)
                elif (c + 1) * CHUNK[key[0]] >= CAP[key[0]]:
                    s["stopped"] = ("cap", c)
                c += 1

        for key in state:
            submit(key)
        while pending:
            time.sleep(1)
            for result in [r for r in pending if r.ready()]:
                pending.remove(result)
                (d, model, n, chunk, _), errors, accepted = result.get()
                key = (d, model, n)
                s = state[key]
                was = s["stopped"]
                s["done"][chunk] = (errors, accepted)
                settle(key)
                if s["stopped"] is None:
                    if time.time() - start > CEILING_S:
                        prefix = 0
                        while prefix in s["done"]:
                            prefix += 1
                        s["stopped"] = ("ceiling", prefix - 1)
                    else:
                        # Keep up to three chunks of a point in flight.
                        inflight = s["next"] - len(s["done"])
                        for _ in range(max(0, 3 - inflight)):
                            if s["next"] * CHUNK[d] < CAP[d]:
                                submit(key)
                if s["stopped"] and not was:
                    print(f"d={d} {model:<10} n={n} stopped "
                          f"({s['stopped'][0]}) after {s['stopped'][1] + 1} "
                          f"chunks, "
                          f"{time.time() - start:6.0f}s", flush=True)
            if (time.time() - start > CEILING_S
                    and all(s["stopped"] for s in state.values())):
                pool.terminate()
                break
    return points, state


def main() -> int:
    from analyze_p02 import analyse
    from measure_p01 import environment
    from starlab import branch_flip_shape, ideal_acceptance, physical_angle
    from starlab.stats import rate_record

    today = datetime.date.today().isoformat()
    out = ROOT / "data" / "results"
    checks = validation()
    (out / "p02_validation.json").write_text(json.dumps(
        {"protocol": "P02", "captured": today,
         "seed": "none: deterministic checks",
         "environment": environment(), **checks}, indent=2) + "\n",
        encoding="utf-8")
    print(f"V1 {'pass' if checks['V1_pass'] else 'FAIL'}; V2 pass; "
          f"p_ph(Table II) = {checks['V3']['p_ph_table_ii']:.3e}",
          flush=True)
    if not checks["V1_pass"]:
        print("V1 fails: P02 stops before measuring")
        return 1

    points, state = measure()
    records = []
    for d, model, n, role in points:
        s = state[(d, model, n)]
        how, last = s["stopped"]
        used = [s["done"][c] for c in range(last + 1)]
        errors = sum(e for e, _ in used)
        accepted = sum(a for _, a in used)
        theta = math.pi / 2 ** n
        rec = rate_record(errors, accepted)
        rec.update({
            "d": d, "model": model, "n": n, "role": role,
            "theta_rad": theta, "shots_sampled": CHUNK[d] * len(used),
            "acceptance": accepted / (CHUNK[d] * len(used)),
            "ideal_acceptance": ideal_acceptance(
                physical_angle(theta / math.pi, d), d),
            "shape": branch_flip_shape(theta, d), "chunks": len(used),
            "chunk_shots": CHUNK[d], "stopped_by": how,
            "seed_first": seed(d, model, n, 0)})
        records.append(rec)
    analysis = analyse(records, MODELS[2:], DISTANCES)
    (out / "p02_injection_error.json").write_text(json.dumps(
        {"protocol": "P02", "captured": today,
         "seed_base": "1e6 d + 1e4 m + 100 n + chunk", "models": MODELS,
         "environment": environment(), "points": records,
         "analysis": analysis}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(analysis, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
