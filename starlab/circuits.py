"""QuEra's STAR injection circuits, at any angle.

The circuits come from QuEra's ETH QHack 2026 challenge (fetched and
hash-checked by tools/fetch_star_circuits.py). Each one prepares a
distance-d rotated surface-code patch in logical |+>, applies k = d physical
Z rotations along a logical-Z string, post-selects on three rounds of
syndrome extraction, runs d more rounds, and then -- with noise switched off
-- applies the exact inverse logical rotation and measures logical X. A 1 in
that last measurement is a logical error.

Each file holds exactly two R_Z lines: the physical rotations, before the
TICK[DISABLE_ERROR] marker, and the single-qubit logical unrotation after
it. Changing the angle means rewriting both, consistently, which is all this
module does.

Angles inside .stim text are in units of pi (tsim's convention); the public
functions here take radians unless the name says `_in_pi`.
"""

from __future__ import annotations

import functools
import math
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
CIRCUITS = ROOT / "data" / "external" / "eth_qhack_2026"

DISTANCES = (3, 5, 7, 9, 11, 13, 15)

_RZ = re.compile(r"^R_Z\(([-+0-9.eE]+)\)((?:\s+\d+)+)\s*$", re.M)
_NOISE_OFF = "TICK[DISABLE_ERROR]"


def physical_angle(logical_angle_in_pi: float, k: int) -> float:
    """Physical angle (units of pi) giving a logical rotation on k qubits.

    QuEra's function from the challenge statement, unchanged: rotating each
    of k qubits on a logical-Z string by theta* and post-selecting on the
    stabilizers leaves the logical rotation tan(theta/2) = tan^k(theta*/2),
    with a sign that alternates with (k - 1)/2 (Chapter 2 derives it).
    """
    assert k % 2 == 1 and k > 0, "k must be a positive odd integer"
    sign = -1 if (k + 1) % 4 == 0 else 1
    x = math.tan(logical_angle_in_pi * math.pi / 2) ** (1 / k)
    return float(sign * 2 * math.atan(x) / math.pi)


def logical_angle(physical_angle_in_pi: float, k: int) -> float:
    """The inverse of `physical_angle`: the logical angle, units of pi."""
    sign = -1 if (k + 1) % 4 == 0 else 1
    half = abs(physical_angle_in_pi) * math.pi / 2
    return float(sign * math.copysign(1, physical_angle_in_pi)
                 * 2 * math.atan(math.tan(half) ** k) / math.pi)


def ideal_acceptance(physical_angle_in_pi: float, k: int) -> float:
    """Noiseless post-selection rate: cos^2k(theta*/2) + sin^2k(theta*/2)."""
    half = physical_angle_in_pi * math.pi / 2
    return math.cos(half) ** (2 * k) + math.sin(half) ** (2 * k)


def n_postselected(d: int) -> int:
    """Detectors that must all be zero for an injection to be accepted."""
    return 3 * (d * d - 1)


@functools.lru_cache(maxsize=None)
def source(d: int) -> str:
    """The published circuit text for distance d, as fetched."""
    path = CIRCUITS / f"star_d={d}.stim"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} is missing. Run `make fetch` (or python "
            "tools/fetch_star_circuits.py) first.")
    return path.read_text(encoding="utf-8")


def with_angle(text: str, d: int, theta_rad: float) -> str:
    """Rewrite a STAR circuit so it injects logical angle `theta_rad`."""
    noise_off = text.index(_NOISE_OFF)
    found = list(_RZ.finditer(text))
    before = [m for m in found if m.start() < noise_off]
    after = [m for m in found if m.start() > noise_off]
    if len(before) != 1 or len(after) != 1:
        raise ValueError(f"expected one physical and one logical R_Z line, "
                         f"found {len(before)} and {len(after)}")
    phys, unrot = before[0], after[0]
    if len(phys.group(2).split()) != d or len(unrot.group(2).split()) != 1:
        raise ValueError("R_Z target counts do not match distance d")

    in_pi = theta_rad / math.pi
    new_phys = f"R_Z({physical_angle(in_pi, d)!r}){phys.group(2)}"
    new_unrot = f"R_Z({-in_pi!r}){unrot.group(2)}"
    return (text[:phys.start()] + new_phys + text[phys.end():unrot.start()]
            + new_unrot + text[unrot.end():])


def star_text(d: int, theta_rad: float) -> str:
    """The published distance-d circuit, set to inject `theta_rad`."""
    return with_angle(source(d), d, theta_rad)


def star_circuit(d: int, theta_rad: float, noiseless: bool = False):
    """A tsim.Circuit for distance d at logical angle `theta_rad`."""
    import tsim

    circuit = tsim.Circuit(star_text(d, theta_rad))
    return circuit.without_noise() if noiseless else circuit
