"""Recover the numbers behind QuEra's STAR reference plot from its SVG.

Protocol P01 asks whether this book's pipeline reproduces the uniform-noise
STAR curve QuEra published for ETH QHack 2026. A reproduction needs numbers
to be compared against, fixed before any of this book's own numbers exist.

The plot is a Matplotlib SVG, so its data are not pixels to be eyeballed:
every marker is placed at an exact coordinate, and every major tick carries
its label in a comment. Two ticks per axis fix the log-scale mapping, and the
markers then convert to values to about four significant figures.

Writes data/reference/eth_qhack_2026_star_sim.json (committed).

Run:  python tools/digitize_reference.py
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SVG = ROOT / "data" / "external" / "eth_qhack_2026" / "star_sim.svg"
OUT = ROOT / "data" / "reference" / "eth_qhack_2026_star_sim.json"

TICK = re.compile(r'<g id="(x|y)tick_\d+">.*?<use xlink:href="#[^"]+" '
                  r'x="([\d.]+)" y="([\d.]+)".*?<!-- \$\\mathdefault\{10\^\{'
                  r'(-?\d+)\}\}\$ -->', re.S)
LINE = re.compile(r'<g id="line2d_\d+">(.*?)</g>', re.S)
MARK = re.compile(r'<use xlink:href="#[^"]+" x="([\d.]+)" y="([\d.]+)" '
                  r'style="[^"]*stroke: (#[0-9a-f]{6})')

# Legend order in the SVG: d=3 blue, d=5 vermillion, d=7 green.
DISTANCE_BY_COLOUR = {"#0072b2": 3, "#d55e00": 5, "#009e73": 7}


def axis_map(ticks):
    """Pixel -> log10(value) from the first two labelled ticks."""
    (p0, e0), (p1, e1) = ticks[:2]
    slope = (e1 - e0) / (p1 - p0)
    return lambda p: e0 + (p - p0) * slope


def main() -> int:
    svg = SVG.read_text(encoding="utf-8")
    xt, yt = [], []
    for axis, x, y, exponent in TICK.findall(svg):
        (xt if axis == "x" else yt).append(
            (float(x) if axis == "x" else float(y), int(exponent)))
    to_x, to_y = axis_map(xt), axis_map(yt)

    curves = {}
    for body in LINE.findall(svg):
        marks = MARK.findall(body)
        if len(marks) < 5:          # tick marks and legend swatches
            continue
        d = DISTANCE_BY_COLOUR[marks[0][2]]
        curves[d] = [{"theta_rad": 10 ** to_x(float(x)),
                      "logical_error_per_distance": 10 ** to_y(float(y))}
                     for x, y, _ in marks]

    record = {
        "source": "QuEraComputing/ETH_QHACK_2026 assets/star_sim.svg",
        "svg_sha256": hashlib.sha256(SVG.read_bytes()).hexdigest(),
        "noise": "uniform depolarizing p = 1e-3 (as in the published .stim)",
        "y_quantity": "logical error rate / distance",
        "theta_grid_log10": [round(math.log10(p["theta_rad"]), 4)
                             for p in curves[3]],
        "curves": {f"d={d}": curves[d] for d in sorted(curves)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    for d in sorted(curves):
        values = ", ".join(f"{p['logical_error_per_distance']:.2e}"
                           for p in curves[d])
        print(f"d={d}: {values}")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
