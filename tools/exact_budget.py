"""The exact first-order error budget, d = 3 to 15 (Chapter 12).

Computed, not sampled: `starlab.enumerate` at theta = pi/16 under Table II
scaled to p_ph = 1e-3 (P02's model T) and the published uniform model,
noise in the injection window. Valid to first order. P03 tested the
calculation against 665 M sampled shots at d = 3 and 5, and P04 tests its
per-row budget and d = 7 blind. Chapter 12 reports these numbers only
under those two verdicts.

For each distance it records:
- each Table II row's share of the injection error;
- A/p for both models, and alpha = (A/p) S_k (Chapter 9);
- the CZ channel's sensitivity to its three Table II parameters: a single
  X or Y on either atom (p_XY), a single Z (p_Z), and the correlated ZZ
  (p_ZZ). Each is dA/dp per unit of that parameter, in both Hadamard
  compilations.

Writes data/results/exact_budget.json. Run:
    nice -n 19 python tools/exact_budget.py
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
from starlab import branch_flip_shape, star_text          # noqa: E402
from starlab import renoise as rn                         # noqa: E402
from starlab.enumerate import injection_error, matches    # noqa: E402

THETA = math.pi / 16
DISTANCES = (3, 5, 7, 9, 11, 13, 15)
NAMES = "IX IY IZ XI XX XY XZ YI YX YY YZ ZI ZX ZY ZZ".split()
GROUPS = {"p_XY": ("IX", "XI", "IY", "YI"), "p_Z": ("IZ", "ZI"),
          "p_ZZ": ("ZZ",)}


def s_k(k: int) -> float:
    return sum(2**j * branch_flip_shape(math.pi / 2**j, k)
               for j in range(2, 80)) / math.pi


def budget(d: int) -> dict:
    clean = {h: rn.renoise(star_text(d, THETA), d, (), hadamards=h)
             for h in ("minimal", "naive")}

    def rate(model, hadamards="minimal"):
        text = rn.renoise(star_text(d, THETA), d, model,
                          window="injection", hadamards=hadamards)
        return injection_error(matches(text, clean[hadamards])[0],
                               THETA, d)

    f = branch_flip_shape(THETA, d)
    full = rn.table_ii(1e-3)
    total, uniform = rate(full), rate(rn.uniform(1e-3))
    rows = sorted({row for row, _, _ in full})
    shares = {row: rate(rn.only(full, row)) / total for row in rows}
    sens = {}
    for hadamards in ("minimal", "naive"):
        per_term = {}
        for i, name in enumerate(NAMES):
            args = [0.0] * 15
            args[i] = 1e-4
            one = (("CZ gate", "cz", rn.Channel("PAULI_CHANNEL_2",
                                                tuple(args))),)
            per_term[name] = rate(one, hadamards) / 1e-4 / f
        sens[hadamards] = {
            "per_term_pair_order": per_term,
            "groups": {g: sum(per_term[t] for t in terms)
                       for g, terms in GROUPS.items()}}
    return {"d": d, "A_T_over_p": total / f / 1e-3,
            "A_U_over_p": uniform / f / 1e-3, "T_over_U": total / uniform,
            "S_k": s_k(d), "alpha_T": total / f / 1e-3 * s_k(d),
            "alpha_U": uniform / f / 1e-3 * s_k(d), "shares": shares,
            "cz_sensitivity": sens}


def main() -> int:
    out = []
    for d in DISTANCES:
        b = budget(d)
        out.append(b)
        g = b["cz_sensitivity"]["minimal"]["groups"]
        print(f"d={d:>2}  A_T/p {b['A_T_over_p']:5.2f}  alpha_T "
              f"{b['alpha_T']:5.2f}  1q {b['shares']['1q gate']:.3f}  "
              f"CZ dA/dp: XY {g['p_XY']:.0f} Z {g['p_Z']:.0f} "
              f"ZZ {g['p_ZZ']:.0f}", flush=True)
    record = {"computed_by": "tools/exact_budget.py (starlab.enumerate)",
              "captured": datetime.date.today().isoformat(),
              "seed": "none: deterministic enumeration",
              "theta_rad": THETA, "environment": environment(),
              "budget": out}
    path = ROOT / "data" / "results" / "exact_budget.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
