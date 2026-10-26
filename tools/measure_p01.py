"""Run Protocol P01: reproduce QuEra's uniform-noise STAR curve.

Executes exactly what protocols/P01-reproduce-uniform-star.md registers and
writes one artifact per distance to data/results/. The protocol is the
specification; this script is only its execution, so any change here after
registration is a deviation and goes in the protocol's Deviations section.

Run:  python tools/measure_p01.py            (both distances)
      python tools/measure_p01.py --d 3      (one distance)
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import pathlib
import platform
import sys
import time
from importlib import metadata

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from starlab import ideal_acceptance, physical_angle    # noqa: E402
from starlab.sampling import sample_star                 # noqa: E402

THETAS = [10 ** (-4 + 0.6 * i) for i in range(8)]
SHOTS = {3: 1_000_000, 5: 4_000_000}
REFERENCE = ROOT / "data" / "reference" / "eth_qhack_2026_star_sim.json"


def environment() -> dict:
    found = {"python": platform.python_version(),
             "platform": platform.platform()}
    for package in ("numpy", "stim", "PyMatching", "bloqade-tsim", "jax"):
        try:
            found[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            found[package] = None
    return found


def run(d: int) -> pathlib.Path:
    reference = json.loads(REFERENCE.read_text())["curves"][f"d={d}"]
    points = []
    for i, theta in enumerate(THETAS):
        seed = 20261026 + 1000 * d + i
        start = time.time()
        record = sample_star(d, theta, SHOTS[d], seed)
        record["seconds"] = round(time.time() - start, 1)
        record["per_distance"] = record["logical_error_rate"] / d
        record["reference_per_distance"] = \
            reference[i]["logical_error_per_distance"]
        record["ideal_acceptance"] = ideal_acceptance(
            physical_angle(theta / math.pi, d), d)
        points.append(record)
        print(f"d={d} θ={theta:.3e}  acc={record['acceptance']:.4f} "
              f"(ideal {record['ideal_acceptance']:.4f})  "
              f"errors={record['logical_errors']}/{record['shots']}  "
              f"rate/d={record['per_distance']:.3e}  "
              f"ref={record['reference_per_distance']:.3e}  "
              f"[{record['seconds']}s]", flush=True)

    artifact = {
        "protocol": "P01",
        "captured": datetime.date.today().isoformat(),
        "seed_base": 20261026 + 1000 * d,
        "environment": environment(),
        "d": d,
        "noise": "as published (uniform depolarizing, p = 1e-3)",
        "points": points,
    }
    out = ROOT / "data" / "results" / f"p01_uniform_star_d{d}.json"
    out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--d", type=int, choices=sorted(SHOTS))
    args = parser.parse_args()
    for d in ([args.d] if args.d else sorted(SHOTS)):
        run(d)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
