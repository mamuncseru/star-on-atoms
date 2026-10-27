"""Tests for starlab: the library must be right before any number is.

Every test here checks the library against something that already exists
independently of it -- the angles QuEra wrote into its own circuit files,
the closed-form STAR algebra of Chapter 6, or textbook statistics. None of
them is an experimental result, so none needs a protocol.

Run:  python tests/test_starlab.py      (or: pytest tests/)
"""

from __future__ import annotations

import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np                                          # noqa: E402

import starlab                                              # noqa: E402
from starlab.circuits import source                         # noqa: E402

# The physical angle (units of pi) QuEra wrote into each published circuit,
# for a logical rotation of 0.01*pi.
PUBLISHED = {3: -0.1562269946295373, 5: 0.2616095711649016,
             7: -0.3213254571082384, 9: 0.35805278613072095}


def test_physical_angle_matches_published_circuits():
    for d, want in PUBLISHED.items():
        got = starlab.physical_angle(0.01, d)
        assert math.isclose(got, want, rel_tol=1e-12), (d, got, want)


def test_logical_angle_inverts_physical_angle():
    for k in (1, 3, 5, 7, 9):
        for theta in (1e-4, 3e-3, 0.01, 0.1, 0.4):
            back = starlab.logical_angle(starlab.physical_angle(theta, k), k)
            assert math.isclose(back, theta, rel_tol=1e-9), (k, theta, back)


def test_with_angle_reproduces_the_published_text():
    for d in PUBLISHED:
        text = starlab.with_angle(source(d), d, 0.01 * math.pi)
        angles = [float(a) for a in re.findall(r"^R_Z\(([-0-9.e]+)\)",
                                               text, re.M)]
        assert math.isclose(angles[0], PUBLISHED[d], rel_tol=1e-12)
        assert math.isclose(angles[1], -0.01, rel_tol=1e-12)


def test_ideal_acceptance_limits():
    assert starlab.ideal_acceptance(0.0, 3) == 1.0
    # theta* = pi/2 on k qubits: every Z-string term has weight 2^-k.
    assert math.isclose(starlab.ideal_acceptance(0.5, 3), 2 * 0.5 ** 3)


def test_noiseless_star_accepts_at_the_ideal_rate_and_never_fails():
    shots = 20_000
    for d in (3, 5):
        theta = 0.2                                    # radians, logical
        circuit = starlab.star_circuit(d, theta, noiseless=True)
        sampler = circuit.compile_detector_sampler(seed=7)
        dets, obs = sampler.sample(shots, separate_observables=True)
        dets, obs = np.asarray(dets, bool), np.asarray(obs, bool)
        keep = ~dets[:, :starlab.n_postselected(d)].any(axis=1)
        want = starlab.ideal_acceptance(
            starlab.physical_angle(theta / math.pi, d), d)
        sigma = math.sqrt(want * (1 - want) / shots)
        assert abs(keep.mean() - want) < 5 * sigma, (d, keep.mean(), want)
        # Detectors after the injection rounds are silent without noise...
        assert not dets[keep][:, starlab.n_postselected(d):].any()
        # ...and the perfect unrotation returns every accepted shot to |+>.
        assert not obs[keep, 0].any()


def test_restrict_noise_partitions_the_published_noise():
    from starlab.circuits import restrict_noise
    for d in (3, 5):
        text = source(d)
        total = sum(line.startswith("DEPOLARIZE")
                    for line in text.splitlines())
        inj = restrict_noise(text, d, "injection")
        mem = restrict_noise(text, d, "memory")
        count = [sum(line.startswith("DEPOLARIZE")
                     for line in t.splitlines()) for t in (inj, mem)]
        assert count[0] + count[1] == total and min(count) > 0, (d, count)
        # Only noise lines differ: the gate-and-detector skeleton is intact.
        strip = [[line for line in t.splitlines()
                  if not line.startswith("DEPOLARIZE")]
                 for t in (text, inj, mem)]
        assert strip[0] == strip[1] == strip[2]
        # The boundary is the last post-selected detector: no injection
        # noise after it, no memory noise before it.
        def noise_detector_positions(t):
            seen, before, after = 0, 0, 0
            for line in t.splitlines():
                if line.startswith("DETECTOR"):
                    seen += 1
                elif line.startswith("DEPOLARIZE"):
                    if seen < starlab.n_postselected(d):
                        before += 1
                    else:
                        after += 1
            return before, after
        assert noise_detector_positions(inj)[1] == 0
        assert noise_detector_positions(mem)[0] == 0


def test_wilson_interval():
    # At zero failures the lower end is zero only up to rounding (the same
    # slack tools/check_results.py allows); the upper end is near 3/n.
    lo, hi = starlab.wilson(0, 1000)
    assert lo < 1e-12 and 0.003 < hi < 0.004
    lo, hi = starlab.wilson(50, 100)
    assert lo < 0.5 < hi and math.isclose(lo + hi, 1.0)
    record = starlab.rate_record(3, 1000)
    assert record["logical_error_rate"] == 0.003
    assert record["wilson_95"][0] < 0.003 < record["wilson_95"][1]


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in sorted(globals().items())
             if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        print(f"  ✓ {name}")
    print(f"{len(tests)} starlab tests passed.")
