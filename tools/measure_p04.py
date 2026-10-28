"""Run Protocol P04: the sampled error budget, as a blind test of P03.

Two stages, as protocols/P04-sampled-budget-blind-test.md registers:

    python tools/measure_p04.py --predict   # before registration: writes
                                            # data/predictions/p04_exact.json
    nice -n 19 taskset -c 0-31 python tools/measure_p04.py

The second stage samples every arm (Table II at p_ph = 1e-3 unless
stated, injection window, every detector post-selected) and scores it
against the committed predictions. It writes
data/results/p04_sampled_budget.json.
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

PREDICTIONS = ROOT / "data" / "predictions" / "p04_exact.json"
P02 = ROOT / "data" / "results" / "p02_injection_error.json"
CHUNK = {3: 1_000_000, 5: 2_000_000, 7: 2_000_000}
MAIN_ROWS = ("1q gate", "CZ spectator", "CZ gate")
ZERO_ROWS = ("initialization", "measurement", "CZ loss", "atom move loss")
CONSISTENT, INCONSISTENT = (0.92, 1.08), (0.85, 1.18)


def arms() -> dict:
    """Every registered arm: key -> spec."""
    out = {}
    for d in (3, 5):
        for row in MAIN_ROWS:
            out[f"d{d} {row}"] = {"d": d, "n": 4, "rows": [row],
                                  "kind": "main", "target": 400,
                                  "cap": 2 * 10**8}
        out[f"d{d} atom move"] = {"d": d, "n": 4, "rows": ["atom move"],
                                  "kind": "small", "target": 10**9,
                                  "cap": 4 * 10**7}
        for row in ZERO_ROWS:
            out[f"d{d} {row}"] = {"d": d, "n": 4, "rows": [row],
                                  "kind": "zero", "target": 10**9,
                                  "cap": 2 * 10**7}
        out[f"d{d} s=1 all-on"] = {"d": d, "n": 4, "rows": None,
                                   "p_ph": None, "kind": "report",
                                   "target": 10**9,
                                   "cap": 2 * 10**6 * (1 + (d == 5))}
    out["d5 1q gate x0.5"] = {"d": 5, "n": 4, "rows": None,
                              "halve": "1q gate", "kind": "main",
                              "target": 1000, "cap": 3 * 10**8}
    out["d3 1q gate pi/64"] = {"d": 3, "n": 6, "rows": ["1q gate"],
                               "kind": "main", "target": 400,
                               "cap": 2 * 10**8}
    out["d7 all-on"] = {"d": 7, "n": 4, "rows": None, "kind": "main",
                        "target": 400, "cap": 1.6 * 10**8}
    for i, (key, spec) in enumerate(out.items()):
        spec["index"] = i
    return out


def model(spec):
    from starlab import renoise as rn
    base = rn.table_ii(spec.get("p_ph", 1e-3))
    if spec.get("halve"):
        return tuple((row, role, c.scaled(0.5) if row == spec["halve"]
                      else c) for row, role, c in base)
    return base if spec["rows"] is None else rn.only(base, spec["rows"])


def text_for(spec, noise=True) -> str:
    from starlab import renoise as rn
    from starlab import star_text
    d, theta = spec["d"], math.pi / 2 ** spec["n"]
    return rn.renoise(star_text(d, theta), d, model(spec) if noise else (),
                      window="injection")


def worker(task):
    key, chunk, shots, seed = task
    import tsim
    from starlab.sampling import sample_injection
    rec = sample_injection(tsim.Circuit(text_for(arms()[key])), shots, seed)
    return task, rec["logical_errors"], rec["shots"]


def predict() -> dict:
    from starlab.enumerate import injection_error, matches
    out = {}
    for key, spec in arms().items():
        found, census = matches(text_for(spec), text_for(spec, noise=False))
        out[key] = {"predicted_rate": injection_error(
            found, math.pi / 2 ** spec["n"], spec["d"]), "census": census}
    return out


def score(rec, spec, pred, all_on) -> dict:
    lo, hi = rec["wilson_95"]
    c = pred["predicted_rate"]
    if spec["kind"] == "main":
        ok = lo * CONSISTENT[0] <= c <= hi * CONSISTENT[1]
        bad = c < lo * INCONSISTENT[0] or c > hi * INCONSISTENT[1]
        return {"consistent": ok, "inconsistent": bad,
                "predicted_over_measured": c / rec["logical_error_rate"]
                if rec["logical_errors"] else None}
    if spec["kind"] == "zero":
        return {"share_upper": hi / all_on, "share_lower": lo / all_on,
                "consistent": hi / all_on < 0.01,
                "inconsistent": lo / all_on > 0.01}
    if spec["kind"] == "small":
        from scipy.stats import poisson
        mu = c * rec["shots"]
        lo_q, hi_q = poisson.ppf(0.005, mu), poisson.ppf(0.995, mu)
        ok = lo_q <= rec["logical_errors"] <= hi_q
        return {"expected_errors": mu, "poisson_99": [lo_q, hi_q],
                "consistent": bool(ok), "inconsistent": False}
    return {"consistent": True, "inconsistent": False,
            "predicted_over_measured": c / rec["logical_error_rate"]
            if rec["logical_errors"] else None}


def main() -> int:
    if "--predict" in sys.argv:
        PREDICTIONS.parent.mkdir(parents=True, exist_ok=True)
        PREDICTIONS.write_text(json.dumps(predict(), indent=2) + "\n",
                               encoding="utf-8")
        print(f"wrote {PREDICTIONS.relative_to(ROOT)}")
        return 0

    import chunked
    from measure_p01 import environment
    from starlab import ideal_acceptance, physical_angle
    from starlab.stats import rate_record

    preds = json.loads(PREDICTIONS.read_text(encoding="utf-8"))
    specs = arms()
    points = {key: {"chunk": CHUNK[s["d"]], "target": s["target"],
                    "cap": s["cap"],
                    "seed": (lambda c, i=s["index"]: 10**7 + 10**5 * i + c)}
              for key, s in specs.items()}
    results = chunked.run(points, worker)
    p02 = json.loads(P02.read_text(encoding="utf-8"))
    all_on = {p["d"]: p for p in p02["points"]
              if p["model"] == "T" and p["n"] == 4}
    records = []
    for key, spec in specs.items():
        how, used = results[key]
        errors = sum(e for e, _ in used)
        accepted = sum(a for _, a in used)
        theta = math.pi / 2 ** spec["n"]
        rec = rate_record(errors, accepted)
        rec.update({"arm": key, "d": spec["d"], "n": spec["n"],
                    "theta_rad": theta, "kind": spec["kind"],
                    "shots_sampled": CHUNK[spec["d"]] * len(used),
                    "acceptance": accepted / (CHUNK[spec["d"]] * len(used)),
                    "ideal_acceptance": ideal_acceptance(
                        physical_angle(theta / math.pi, spec["d"]),
                        spec["d"]),
                    "stopped_by": how, "chunks": len(used),
                    "seed_first": points[key]["seed"](0),
                    "predicted_rate": preds[key]["predicted_rate"]})
        ref = all_on.get(spec["d"])
        rec["score"] = score(rec, spec, preds[key],
                             ref["logical_error_rate"] if ref else None)
        records.append(rec)
        print(f"{key:<22} {errors:>5} / {accepted:>10}  "
              f"rate {rec['logical_error_rate']:.3e}  "
              f"C {preds[key]['predicted_rate']:.3e}  {rec['score']}",
              flush=True)
    scored = [r for r in records if r["kind"] != "report"]
    if any(r["score"]["inconsistent"] for r in scored):
        verdict = "REFUTED"
    elif all(r["score"]["consistent"] for r in scored):
        verdict = "CONFIRMED"
    else:
        verdict = "INCONCLUSIVE"
    additivity = {}
    for d in (3, 5):
        rows = [r for r in records if r["d"] == d and r["n"] == 4
                and r["kind"] in ("main", "small", "zero")
                and "x0.5" not in r["arm"]]
        additivity[str(d)] = (sum(r["logical_error_rate"] for r in rows)
                              / all_on[d]["logical_error_rate"])
    record = {"protocol": "P04", "captured": datetime.date.today().isoformat(),
              "seed_base": "1e7 + 1e5 arm + chunk",
              "environment": environment(), "arms": records,
              "summary": {"verdict": verdict,
                          "sampled_sum_over_P02_all_on": additivity}}
    out = ROOT / "data" / "results" / "p04_sampled_budget.json"
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
