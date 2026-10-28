"""The injection error to first order, exactly, by enumerating faults.

Protocol P02 found the injection error of the published STAR circuits to be
one constant times the misrotation shape: single faults that post-selection
cannot see because a rotation branch hides them (Chapter 11). This module
computes that error with no sampling (Chapter 12, Protocol P03).

1. In the theta = 0 Clifford proxy (stim reads every R_Z as an identity),
   the detector error model lists every fault mechanism E: its probability
   p_E, the detectors D_E it flips, and whether it flips the X_L
   observable, O_E.
2. A Z on rotated qubit j, placed at the rotation, has its own symptom
   (D_j, O_j). The rotation puts the patch into branches Z_S, S a subset of
   the rotated qubits K, with symptom D_S = XOR of D_j over S.
3. With every detector post-selected, E survives only with a branch that
   cancels it: D_E = D_S. The branches with that symptom are exactly S and
   K - S (Z_K is the logical Z_L, which flips no detector), and the
   observable bit picks which one E acts as: S* with O_S* = O_E.
4. E then fails with probability `branch_weight(theta, k, |S*|)`: the
   chance that the branches S* and K - S* survive, times the misrotation
   they carry after the perfect unrotation.

So the first-order injection error is sum_E p_E * branch_weight(...). An E
that matches no branch is detected and only costs acceptance. The method is
the paper's Eq. 2 (arXiv:2509.18294v2), evaluated exactly for these
circuits; it is valid to first order in the fault probabilities, for Pauli
noise, with the rounds after the injection window noiseless.
"""

from __future__ import annotations

import dataclasses
import itertools
import math
import re

from .circuits import physical_angle

_RZ = re.compile(r"^R_Z\([^)]*\)((?:\s+\d+)+)\s*$", re.M)


def branch_weight(theta_rad: float, k: int, m: int) -> float:
    """Failure probability of a fault equivalent to Z on m rotated qubits.

    The branches S* (|S*| = m) and K - S* survive, with probability
    [c^2(k-m) s^2m + c^2m s^2(k-m)] / (c^2k + s^2k), and leave a rotation
    with tan(phi/2) = (-1)^m t^(k-2m) against the intended t^k (t = s/c,
    common sign dropped). m = 1 is `branch_flip_shape`; m = 0 never fails;
    m = k is a logical Z and always fails.
    """
    half = abs(physical_angle(theta_rad / math.pi, k)) * math.pi / 2
    c, s = math.cos(half), math.sin(half)
    t = s / c
    survive = ((c ** (2 * (k - m)) * s ** (2 * m)
                + c ** (2 * m) * s ** (2 * (k - m)))
               / (c ** (2 * k) + s ** (2 * k)))
    wrong = math.sin(math.atan((-1) ** m * t ** (k - 2 * m))
                     - math.atan(t ** k)) ** 2
    return survive * wrong


def _proxy(text: str):
    import tsim
    return tsim.Circuit(text).stim_circuit


def _symptoms(dem):
    """(p, detectors, observable flip) for every error in a DEM."""
    for inst in dem.flattened():
        if inst.type != "error":
            continue
        dets, obs = set(), 0
        for t in inst.targets_copy():
            if t.is_relative_detector_id():
                dets.add(t.val)
            elif t.is_logical_observable_id():
                obs ^= 1
            else:
                raise ValueError(f"unexpected target {t} (decomposed DEM?)")
        yield inst.args_copy()[0], frozenset(dets), obs


def branch_table(noiseless_text: str):
    """The rotated qubits K, and each branch symptom -> its two subsets.

    `noiseless_text` is the circuit with no noise at all. A marker Z after
    the R_Z on each rotated qubit gives (D_j, O_j); branch symptoms are
    XORs of those. Every symptom class must hold exactly {S, K - S}, i.e.
    no Z-stabilizer lies inside K.
    """
    rz = _RZ.search(noiseless_text)
    if rz is None:
        raise ValueError("no R_Z line in the circuit")
    rotated = [int(q) for q in rz.group(1).split()]
    marks = {}
    for j in rotated:
        text = (noiseless_text[:rz.end()] + f"\nZ_ERROR(0.01) {j}"
                + noiseless_text[rz.end():])
        found = list(_symptoms(_proxy(text).detector_error_model()))
        if len(found) != 1:
            raise ValueError(f"marker on qubit {j}: {len(found)} symptoms")
        marks[j] = found[0][1:]
    table = {}
    for size in range(len(rotated) + 1):
        for subset in itertools.combinations(rotated, size):
            dets, obs = frozenset(), 0
            for j in subset:
                dets, obs = dets ^ marks[j][0], obs ^ marks[j][1]
            table.setdefault(dets, []).append((frozenset(subset), obs))
    for dets, members in table.items():
        sizes = sorted(len(s) for s, _ in members)
        if len(members) != 2 or sizes[0] + sizes[1] != len(rotated):
            raise ValueError("a branch symptom class is not {S, K - S}")
    return rotated, table


@dataclasses.dataclass
class Match:
    """One fault mechanism that survives post-selection."""

    p: float
    m: int                       # |S*|: rotated qubits it acts as Z on
    subset: frozenset            # S*


def matches(text: str, noiseless_text: str) -> tuple[list[Match], dict]:
    """Every first-order fault that a branch hides, plus a census.

    `text` carries the noise (normally `window="injection"`); the census
    counts all mechanisms, the detected ones, and any undetectable logical
    error (S* = K), which would be a theta-independent floor.
    """
    rotated, table = branch_table(noiseless_text)
    dem = _proxy(text).detector_error_model(
        decompose_errors=False, approximate_disjoint_errors=True)
    found, census = [], {"mechanisms": 0, "detected": 0, "harmless": 0}
    for p, dets, obs in _symptoms(dem):
        census["mechanisms"] += 1
        if dets not in table:
            census["detected"] += 1
            continue
        subset = next(s for s, o in table[dets] if o == obs)
        if not subset:
            census["harmless"] += 1        # acts as I: no effect at all
            continue
        found.append(Match(p, len(subset), subset))
    census["k"] = len(rotated)
    return found, census


def injection_error(found: list[Match], theta_rad: float, k: int) -> float:
    """First-order injection error at `theta_rad`: sum p * branch_weight."""
    return sum(f.p * branch_weight(theta_rad, k, f.m) for f in found)
