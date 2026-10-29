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


def test_one_z_fault_flips_the_branches_as_derived():
    # The mechanism behind starlab.branch_flip_shape, checked on the real
    # circuit: a certain Z on one rotated qubit, nothing else. Its two
    # factors -- the chance to survive post-selection and the chance the
    # survivor reads out wrong -- must match the derivation.
    import tsim
    from starlab import renoise as rn
    shots, theta = 40_000, 0.3
    for d in (3, 5):
        text = rn.renoise(starlab.star_text(d, theta), d, ())
        rz = re.search(r"^R_Z\(.*\)((?:\s+\d+)+)$", text, re.M)
        j = rz.group(1).split()[0]
        text = text[:rz.end()] + f"\nZ_ERROR(1) {j}" + text[rz.end():]
        sampler = tsim.Circuit(text).compile_detector_sampler(seed=5)
        dets, obs = sampler.sample(shots, separate_observables=True)
        keep = ~np.asarray(dets, bool).any(axis=1)
        wrong = np.asarray(obs, bool)[keep, 0].mean()
        half = abs(starlab.physical_angle(theta / math.pi, d)) * math.pi / 2
        c, s = math.cos(half), math.sin(half)
        t = s / c
        survive = s * s * c ** (2 * d - 2) + c * c * s ** (2 * d - 2)
        flip = math.sin(math.atan(t ** (d - 2)) + math.atan(t ** d)) ** 2
        for got, want, n in ((keep.mean(), survive, shots),
                             (wrong, flip, keep.sum())):
            assert abs(got - want) < 5 * math.sqrt(want * (1 - want) / n), \
                (d, got, want)
    # Small angles: the shape is a power law, theta^(2 - 2/k).
    for k in (3, 5, 7):
        slope = math.log(starlab.branch_flip_shape(2e-12, k)
                         / starlab.branch_flip_shape(1e-12, k)) / math.log(2)
        assert abs(slope - (2 - 2 / k)) < 0.01, (k, slope)


def test_branch_weight_limits_and_m1():
    from starlab.enumerate import branch_weight
    for k in (3, 5, 7):
        for theta in (0.01, 0.1, math.pi / 16, math.pi / 4):
            assert math.isclose(branch_weight(theta, k, 1),
                                starlab.branch_flip_shape(theta, k),
                                rel_tol=1e-12)
            assert branch_weight(theta, k, 0) < 1e-15
            assert math.isclose(branch_weight(theta, k, k), 1.0,
                                rel_tol=1e-12)


def _planted(d, theta, line):
    """The noiseless native circuit with one fault line after the R_Z."""
    from starlab import renoise as rn
    clean = rn.renoise(starlab.star_text(d, theta), d, ())
    rz = re.search(r"^R_Z\(.*\)((?:\s+\d+)+)$", clean, re.M)
    return clean[:rz.end()] + "\n" + line + clean[rz.end():], clean


def test_enumeration_classifies_planted_faults():
    # Unit tests of the matching logic only: each circuit carries one
    # planted fault and no noise model, so no P02 quantity is computed.
    from starlab.enumerate import branch_table, matches
    theta = 0.3
    for d in (3, 5):
        _, clean = _planted(d, theta, "")
        rotated, table = branch_table(clean)
        assert len(rotated) == d and len(table) == 2 ** (d - 1)
        for j in rotated:
            found, _ = matches(_planted(d, theta, f"Z_ERROR(0.001) {j}")[0],
                               clean)
            assert [(f.m, set(f.subset)) for f in found] == [(1, {j})]
            found, census = matches(
                _planted(d, theta, f"X_ERROR(0.001) {j}")[0], clean)
            assert found == [] and census["detected"] == 1
    _, clean = _planted(3, theta, "")
    # Z0 Z1 is a boundary Z-stabilizer at d = 3, so Z1 acts as Z0.
    found, _ = matches(_planted(3, theta, "Z_ERROR(0.001) 1")[0], clean)
    assert [(f.m, set(f.subset)) for f in found] == [(1, {0})]
    # Two rotated qubits: m = 2, picked by the observable bit.
    found, _ = matches(_planted(3, theta, "E(0.001) Z0 Z3")[0], clean)
    assert [(f.m, set(f.subset)) for f in found] == [(2, {0, 3})]
    # The whole string is a logical Z: undetectable, always fails.
    found, _ = matches(_planted(3, theta, "E(0.001) Z0 Z3 Z6")[0], clean)
    assert [(f.m, set(f.subset)) for f in found] == [(3, {0, 3, 6})]


def test_proxy_reads_the_rotation_as_the_identity():
    # The exact count works in the theta = 0 proxy, so the proxy's error
    # model must be the circuit's with the R_Z lines deleted. tsim issue
    # #226: stim sees R_Z as the identity, but R_ZZ / R_PAULI as S at any
    # angle, so a circuit rotating with those would fail this test.
    from starlab import renoise as rn
    from starlab.enumerate import _proxy
    for d in (3, 5, 7):
        for model in (rn.uniform(1e-3), rn.table_ii(1e-3)):
            text = rn.renoise(starlab.star_text(d, math.pi / 16), d, model,
                              window="injection")
            assert re.search(r"^R_Z\(", text, re.M)
            no_rz = "\n".join(line for line in text.splitlines()
                              if not line.startswith("R_Z("))
            dem = [_proxy(t).detector_error_model(
                decompose_errors=False, approximate_disjoint_errors=True)
                for t in (text, no_rz)]
            assert dem[0] == dem[1]


def test_cz_faults_hide_only_as_the_frame_predicts():
    # Chapter 12's account of P04-R1, planted fault by fault at d = 3. On
    # the ancilla half of any injection-window CZ, a Z or Y is always
    # detected (every ancilla is prepared and measured in X); an X can hide
    # only by spreading through the ancilla's later CZs into Zs on data. On
    # the data half, only an X inside the Hadamard frame or a Z outside it
    # can hide; Y never.
    from starlab import renoise as rn
    from starlab.enumerate import matches
    d = 3
    text = starlab.star_text(d, math.pi / 16)
    cz = next(c for _, role, c in rn.table_ii(1e-3) if role == "cz")
    noisy = rn.renoise(text, d, (("CZ gate", "cz", cz),), window="injection")
    clean_text = rn.renoise(text, d, (), window="injection")
    clean, sites, frame, measured = [], [], {}, {}
    for line in noisy.splitlines():
        if line.startswith("PAULI_CHANNEL_2"):
            qubits = line.split(")", 1)[1].split()
            sites += [(len(clean), q, frame.get(q, 0)) for q in qubits]
            continue
        op, *qubits = line.split() or [""]
        for q in qubits:
            if op == "H":
                frame[q] = frame.get(q, 0) ^ 1
            elif op in ("M", "MX"):
                measured[q] = measured.get(q, 0) + 1
        clean.append(line)

    def hides(pauli, pos, q):
        planted = clean[:pos] + [f"{pauli}_ERROR(0.001) {q}"] + clean[pos:]
        return bool(matches("\n".join(planted), clean_text)[0])

    hidden_by_kind = {"ancilla X": 0, "data X": 0, "data Z": 0}
    for pos, q, in_h in sites:
        hidden = {p for p in "XYZ" if hides(p, pos, q)}
        if measured.get(q, 0) > 1:                     # an ancilla
            assert hidden <= {"X"}
            hidden_by_kind["ancilla X"] += bool(hidden)
        else:
            assert hidden <= ({"X"} if in_h else {"Z"})
            hidden_by_kind["data X" if in_h else "data Z"] += bool(hidden)
    assert len(sites) == 2 * 84 and min(hidden_by_kind.values()) > 0


def test_branch_weight_m2_against_tsim():
    # The m = 2 weight checked on the real circuit, as the m = 1 weight is
    # in test_one_z_fault_flips_the_branches_as_derived.
    import tsim
    from starlab.enumerate import branch_weight
    shots, theta, k = 40_000, 0.3, 3
    text, _ = _planted(k, theta, "E(1) Z0 Z3")
    dets, obs = tsim.Circuit(text).compile_detector_sampler(
        seed=9).sample(shots, separate_observables=True)
    keep = ~np.asarray(dets, bool).any(axis=1)
    half = abs(starlab.physical_angle(theta / math.pi, k)) * math.pi / 2
    c, s = math.cos(half), math.sin(half)
    survive = c ** 2 * s ** 4 + c ** 4 * s ** 2
    wrong = branch_weight(theta, k, 2) * (c ** 6 + s ** 6) / survive
    for got, want, n in ((keep.mean(), survive, shots),
                         (np.asarray(obs, bool)[keep, 0].mean(), wrong,
                          keep.sum())):
        assert abs(got - want) < 5 * math.sqrt(want * (1 - want) / n), \
            (got, want)


def _symptoms(text):
    """A circuit's detector error model as {symptom: probability}, with
    repeated symptoms merged, so two models compare regardless of order."""
    import tsim
    out = {}
    dem = tsim.Circuit(text).stim_circuit.detector_error_model()
    for inst in dem.flattened():
        if inst.type == "error":
            key = tuple(sorted(str(t) for t in inst.targets_copy()))
            p, q = out.get(key, 0.0), inst.args_copy()[0]
            out[key] = p * (1 - q) + q * (1 - p)
    return out


def _gap(a, b):
    return max(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in set(a) | set(b))


def test_uniform_renoise_reproduces_the_published_error_model():
    # P02 check V1: the native rebuild under the published uniform model is
    # the published circuit, fault for fault -- for every compilation
    # variant, since none of them may change where uniform noise lands.
    from starlab import renoise as rn
    for d in (3, 5):
        published = _symptoms(source(d))
        for hadamards in ("minimal", "naive"):
            for mover in ("ancilla", "data"):
                text = rn.renoise(source(d), d, rn.uniform(1e-3),
                                  hadamards=hadamards, mover=mover)
                assert "CX " not in text.split("TICK[DISABLE_ERROR]")[0]
                assert _gap(_symptoms(text), published) < 1e-15, \
                    (d, hadamards, mover)
    # The comparison is not vacuous: leaving out any one role breaks it.
    for role in ("init", "spectator", "feedforward", "idle1", "measure"):
        model = tuple(e for e in rn.uniform(1e-3) if e[1] != role)
        assert _gap(_symptoms(rn.renoise(source(3), 3, model)),
                    _symptoms(source(3))) > 1e-4, role


def test_noiseless_native_circuit_is_the_same_circuit():
    # The rebuild changes gates, not the computation: with no noise it
    # accepts at the ideal rate, never fails, and its later rounds are silent.
    import tsim
    from starlab import renoise as rn
    shots, theta = 20_000, 0.2
    for d in (3, 5):
        want = starlab.ideal_acceptance(
            starlab.physical_angle(theta / math.pi, d), d)
        for hadamards in ("minimal", "naive"):
            text = rn.renoise(starlab.star_text(d, theta), d, (),
                              hadamards=hadamards)
            sampler = tsim.Circuit(text).compile_detector_sampler(seed=11)
            dets, obs = sampler.sample(shots, separate_observables=True)
            dets, obs = np.asarray(dets, bool), np.asarray(obs, bool)
            keep = ~dets[:, :starlab.n_postselected(d)].any(axis=1)
            sigma = math.sqrt(want * (1 - want) / shots)
            assert abs(keep.mean() - want) < 5 * sigma, (d, hadamards)
            assert not dets[keep][:, starlab.n_postselected(d):].any()
            assert not obs[keep, 0].any()


def test_table_ii_accounting():
    # Eq. D1 on Table II gives 7.46e-3 (the paper rounds it to "7.3e-3");
    # scaling hits the requested p_ph exactly and keeps every ratio.
    from starlab import renoise as rn
    assert len(rn.CZ_PAULI) == 15
    assert math.isclose(sum(rn.CZ_PAULI), 4.56e-3)
    assert math.isclose(rn.combined(rn.table_ii()), 7.46e-3)
    model = rn.table_ii(1e-3)
    assert math.isclose(rn.combined(model), 1e-3)
    s = 1e-3 / 7.46e-3
    for (_, _, a), (_, _, b) in zip(rn.table_ii(), model):
        assert all(math.isclose(s * x, y) for x, y in zip(a.args, b.args))
    # Loss acts in the whole entangling zone unless told otherwise.
    roles = [r for row, r, _ in rn.table_ii() if row == "CZ loss"]
    assert roles == ["cz_qubit", "spectator"]
    assert [r for row, r, _ in rn.table_ii(loss_on_spectators=False)
            if row == "CZ loss"] == ["cz_qubit"]
    assert {row for row, _, _ in rn.only(model, "CZ gate")} == {"CZ gate"}


def test_renoise_windows_partition_the_noise():
    from starlab import renoise as rn
    for d in (3, 5):
        def noise_lines(window):
            text = rn.renoise(source(d), d, rn.table_ii(1e-3),
                              window=window)
            return [line for line in text.splitlines()
                    if line.split("(")[0] in rn.NOISE_GATES]
        parts = [noise_lines(w) for w in ("injection", "memory")]
        assert min(map(len, parts)) > 0
        assert sorted(parts[0] + parts[1]) == sorted(noise_lines("all"))


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
