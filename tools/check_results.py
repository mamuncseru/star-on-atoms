"""Every committed measurement carries its evidence.

Commitment 2 of OUTLINE.md: every logical error rate in this book is a
measurement, with its shot count and its interval. A number computed at build
time prints both from the cell that measured it. A number too expensive for a
build is run once by a `tools/measure_*.py` script and committed under
`data/results/` — and a committed JSON file is the one place a number can
quietly lose its provenance, so that is what this guard reads.

Each artifact must record:

  captured      the ISO date it was measured
  seed          `seed` or `seed_base`, so the run can be repeated exactly
  environment   at least the Python version it ran under

and every object anywhere inside it that reports a `logical_error_rate` must
also carry integer `shots` and `logical_errors`, agree with their ratio, and
carry a 95% interval (`wilson_95`) that contains its own estimate.

Run:  python tools/check_results.py
"""

from __future__ import annotations

import datetime
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "data" / "results"

# Floating-point slack for "the interval contains the estimate". A Wilson
# interval at zero observed errors has a lower end that is zero only up to
# rounding.
SLACK = 1e-12


def estimates(node, path="$"):
    """(JSON path, object) for every object that reports a rate."""
    if isinstance(node, dict):
        if "logical_error_rate" in node:
            yield path, node
        for key, value in node.items():
            yield from estimates(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from estimates(value, f"{path}[{index}]")


def problems_in(record) -> list[str]:
    if not isinstance(record, dict):
        return ["the top level is not a JSON object"]

    found = []
    captured = record.get("captured")
    try:
        datetime.date.fromisoformat(str(captured))
    except ValueError:
        found.append(f"`captured` is {captured!r}, not an ISO date")
    if "seed" not in record and "seed_base" not in record:
        found.append("no `seed` or `seed_base`: the run cannot be repeated")
    environment = record.get("environment")
    if not isinstance(environment, dict) or "python" not in environment:
        found.append("no `environment` recording at least `python`")

    for where, point in estimates(record):
        shots, errors = point.get("shots"), point.get("logical_errors")
        rate = point["logical_error_rate"]
        if not isinstance(shots, int) or not isinstance(errors, int):
            found.append(f"{where}: a rate without integer `shots` and "
                         f"`logical_errors`")
            continue
        if shots <= 0 or not 0 <= errors <= shots:
            found.append(f"{where}: {errors} errors in {shots} shots is not "
                         f"a measurement")
            continue
        if abs(rate - errors / shots) > SLACK:
            found.append(f"{where}: rate {rate} is not {errors}/{shots}")
        interval = point.get("wilson_95")
        if not (isinstance(interval, list) and len(interval) == 2):
            found.append(f"{where}: no `wilson_95` interval")
        elif not interval[0] - SLACK <= rate <= interval[1] + SLACK:
            found.append(f"{where}: interval {interval} does not contain "
                         f"its own estimate {rate}")
    return found


def main() -> int:
    artifacts = sorted(RESULTS.glob("*.json"))
    if not artifacts:
        print("No committed measurements yet — nothing to check.")
        return 0

    failures, rates = 0, 0
    for path in artifacts:
        rel = path.relative_to(ROOT)
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            print(f"{rel}: not valid JSON ({error})")
            failures += 1
            continue
        rates += sum(1 for _ in estimates(record))
        for problem in problems_in(record):
            print(f"{rel}: {problem}")
            failures += 1

    print()
    if failures:
        print(f"{failures} evidence problem(s) across {len(artifacts)} "
              f"artifact(s). A rate without its shots and its interval does "
              f"not ship.")
        return 1
    print(f"All {len(artifacts)} artifact(s) carry their evidence: "
          f"{rates} logical error rate(s), each with shots, errors, seed "
          f"and interval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
