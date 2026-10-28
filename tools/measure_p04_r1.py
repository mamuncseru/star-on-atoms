"""Run P04-R1: the CZ channel split into its three Table II parameters.

The calculator predicts that the CZ's correlated ZZ term, its largest,
adds nothing to the injection error, and that its single X/Y terms add more
than its single Z terms. That depends on which atoms sit in the Hadamard
frame during each CZ. Registered in P04's Deviations (2026-10-27) before
running; the same scoring as P04.

    python tools/measure_p04_r1.py --predict
    nice -n 19 taskset -c 0-31 python tools/measure_p04_r1.py

Writes data/predictions/p04_r1_exact.json, then
data/results/p04_r1_cz_terms.json.
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

from measure_p04 import CHUNK, P02, score                  # noqa: E402

PREDICTIONS = ROOT / "data" / "predictions" / "p04_r1_exact.json"
NAMES = "IX IY IZ XI XX XY XZ YI YX YY YZ ZI ZX ZY ZZ".split()
TERMS = {"ZZ only": ("ZZ",), "single Z only": ("IZ", "ZI"),
         "single X/Y only": ("IX", "XI", "IY", "YI")}


def arms() -> dict:
    out = {}
    for d in (3, 5):
        for label, terms in TERMS.items():
            zero = label == "ZZ only"
            out[f"d{d} CZ {label}"] = {
                "d": d, "n": 4, "terms": terms,
                "kind": "zero" if zero else "main",
                "target": 10**9 if zero else 400,
                "cap": 2 * 10**7 if zero else 2 * 10**8}
    for i, spec in enumerate(out.values()):
        spec["index"] = i
    return out


def text_for(spec, noise=True) -> str:
    from starlab import renoise as rn
    from starlab import star_text
    d, theta = spec["d"], math.pi / 2 ** spec["n"]
    model = ()
    if noise:
        cz = next(c for row, role, c in rn.table_ii(1e-3) if role == "cz")
        args = tuple(a if name in spec["terms"] else 0.0
                     for name, a in zip(NAMES, cz.args))
        model = (("CZ gate", "cz", rn.Channel("PAULI_CHANNEL_2", args)),)
    return rn.renoise(star_text(d, theta), d, model, window="injection")


def worker(task):
    key, chunk, shots, seed = task
    import tsim
    from starlab.sampling import sample_injection
    rec = sample_injection(tsim.Circuit(text_for(arms()[key])), shots, seed)
    return task, rec["logical_errors"], rec["shots"]


def main() -> int:
    if "--predict" in sys.argv:
        from starlab.enumerate import injection_error, matches
        preds = {}
        for key, spec in arms().items():
            found, census = matches(text_for(spec), text_for(spec, False))
            preds[key] = {"predicted_rate": injection_error(
                found, math.pi / 2 ** spec["n"], spec["d"]),
                "census": census}
        PREDICTIONS.write_text(json.dumps(preds, indent=2) + "\n",
                               encoding="utf-8")
        for key, v in preds.items():
            print(f"{key:<26} C = {v['predicted_rate']:.3e}")
        return 0

    import chunked
    from measure_p01 import environment
    from starlab.stats import rate_record

    preds = json.loads(PREDICTIONS.read_text(encoding="utf-8"))
    specs = arms()
    points = {key: {"chunk": CHUNK[s["d"]], "target": s["target"],
                    "cap": s["cap"],
                    "seed": (lambda c, i=s["index"]: 2 * 10**7
                             + 10**5 * i + c)}
              for key, s in specs.items()}
    results = chunked.run(points, worker)
    p02 = json.loads(P02.read_text(encoding="utf-8"))
    all_on = {p["d"]: p["logical_error_rate"] for p in p02["points"]
              if p["model"] == "T" and p["n"] == 4}
    records = []
    for key, spec in specs.items():
        how, used = results[key]
        rec = rate_record(sum(e for e, _ in used), sum(a for _, a in used))
        rec.update({"arm": key, "d": spec["d"], "kind": spec["kind"],
                    "theta_rad": math.pi / 2 ** spec["n"],
                    "shots_sampled": CHUNK[spec["d"]] * len(used),
                    "acceptance": rec["shots"] / (CHUNK[spec["d"]]
                                                  * len(used)),
                    "stopped_by": how, "chunks": len(used),
                    "seed_first": points[key]["seed"](0),
                    "predicted_rate": preds[key]["predicted_rate"]})
        rec["score"] = score(rec, spec, preds[key], all_on[spec["d"]])
        records.append(rec)
        print(f"{key:<26} {rec['logical_errors']:>5} / {rec['shots']:>10}"
              f"  rate {rec['logical_error_rate']:.3e}  "
              f"C {rec['predicted_rate']:.3e}  {rec['score']}", flush=True)
    verdict = ("REFUTED" if any(r["score"]["inconsistent"] for r in records)
               else "CONFIRMED" if all(r["score"]["consistent"]
                                       for r in records)
               else "INCONCLUSIVE")
    record = {"protocol": "P04 (diagnostic R1, registered 2026-10-27)",
              "captured": datetime.date.today().isoformat(),
              "seed_base": "2e7 + 1e5 arm + chunk",
              "environment": environment(), "arms": records,
              "summary": {"verdict": verdict}}
    out = ROOT / "data" / "results" / "p04_r1_cz_terms.json"
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("verdict:", verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
