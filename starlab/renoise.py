"""Re-noise QuEra's STAR circuits, one physical channel at a time.

The published circuits carry one uniform model: DEPOLARIZE1(p) and
DEPOLARIZE2(p) after every operation. QuEra's hardware model (PRX Quantum 7,
020343, App. D, Table II) is instead a list of physical channels -- a
Z-biased CZ, atom loss, transport, light on spectators -- defined on the
native gate set. This module rebuilds a circuit in that gate set and puts
each channel where its operation happens (Chapter 11):

    R, RX              init, after the reset
    M, MX              measure, before the measurement
    CX c t             H t, CZ c t, H t: move before the CZ (one atom of
                       each pair), then cz on the pair, cz_qubit on both
                       atoms, spectator on every atom not in a pair
    H                  hadamard, after it
    R_Z                gate1 on the rotated qubits, idle1 on the rest
    CX[FEED_FORWARD]   feedforward on its targets, idle1 on the rest

With `hadamards="minimal"` two Hadamards with nothing between them on a
qubit cancel, and an H next to a reset or measurement folds into it
(R H -> RX, H M -> MX), which is how the paper's Fig. 12 draws syndrome
extraction; only the Hadamards left on data qubits carry noise. With
`"naive"` every Hadamard of the CX -> H CZ H rule is kept, with its noise.

Everything after TICK[DISABLE_ERROR] is copied unchanged. The test of the
machinery is that the uniform model, put through it, reproduces the
published circuit's detector error model exactly (Protocol P02, check V1).
"""

from __future__ import annotations

import dataclasses
import re

from .circuits import n_postselected

NOISE_GATES = ("DEPOLARIZE1", "DEPOLARIZE2", "PAULI_CHANNEL_1",
               "PAULI_CHANNEL_2", "X_ERROR", "Y_ERROR", "Z_ERROR")
_NOISE_OFF = "TICK[DISABLE_ERROR]"
_LINE = re.compile(r"^([A-Z_0-9]+)(\[[^\]]*\])?(?:\(([^)]*)\))?\s*(.*)$")
_COORDS = re.compile(r"^QUBIT_COORDS\(([^)]*)\)\s+(\d+)")


@dataclasses.dataclass(frozen=True)
class Channel:
    """One stim noise instruction and its arguments."""

    gate: str
    args: tuple[float, ...]

    @property
    def total(self) -> float:
        """Total error probability (the sum of a Pauli channel's terms)."""
        return sum(self.args) if self.gate.startswith("PAULI") \
            else self.args[0]

    def scaled(self, s: float) -> "Channel":
        return Channel(self.gate, tuple(s * a for a in self.args))

    def line(self, targets) -> str | None:
        targets = [str(t) for t in targets]
        if not targets or not any(self.args):
            return None
        args = ", ".join(repr(float(a)) for a in self.args)
        return f"{self.gate}({args}) " + " ".join(targets)


# A noise model is a tuple of (Table II row, role, channel). The row names
# the physical process, so a channel can be switched on alone (Protocol
# P03); the role says where the channel goes.
Model = tuple[tuple[str, str, Channel], ...]

ROLES = ("init", "hadamard", "gate1", "feedforward", "idle1", "move", "cz",
         "cz_qubit", "spectator", "measure")


def uniform(p: float) -> Model:
    """The published model: depolarizing p after every operation."""
    d1, d2 = Channel("DEPOLARIZE1", (p,)), Channel("DEPOLARIZE2", (p,))
    return tuple(("uniform", role, d2 if role == "cz" else d1)
                 for role in ("init", "gate1", "feedforward", "idle1", "cz",
                              "spectator", "measure"))


# Table II of arXiv:2509.18294v2 (p. 26), read from the PDF. stim's
# PAULI_CHANNEL_2 order: IX IY IZ XI XX XY XZ YI YX YY YZ ZI ZX ZY ZZ.
CZ_PAULI = (5e-4, 5e-4, 6.3e-4, 5e-4, 0.0, 0.0, 0.0, 5e-4, 0.0, 0.0, 0.0,
            6.3e-4, 0.0, 0.0, 1.3e-3)
P_INIT, P_1Q, P_CZ_LOSS, P_MEASURE = 3e-3, 3e-3, 1.3e-3, 4e-3


def table_ii(p_ph: float | None = None, *, loss_on_spectators: bool = True,
             feedforward_noise: bool = False) -> Model:
    """QuEra's Table II, optionally scaled so that Eq. D1 gives `p_ph`.

    Initialization is depolarizing at 1.5 p_init (App. D a: only two of the
    three Paulis act on a fresh state). The CZ loss acts "on all qubits in
    the entangling zone" (App. D c), spectators included, unless
    `loss_on_spectators` is False. The feed-forward Pauli is a frame update
    (folded into the sign of the next R_Z) and is noiseless unless
    `feedforward_noise` is True, when it costs a 1q gate.
    """
    d1 = Channel("DEPOLARIZE1", (P_1Q,))
    loss = Channel("Y_ERROR", (P_CZ_LOSS,))
    model = [
        ("initialization", "init", Channel("DEPOLARIZE1", (1.5 * P_INIT,))),
        ("1q gate", "gate1", d1),
        ("1q gate", "hadamard", d1),
        ("atom move", "move", Channel("PAULI_CHANNEL_1", (4e-5, 4e-5,
                                                          2e-4))),
        ("atom move loss", "move", Channel("Y_ERROR", (2e-5,))),
        ("CZ gate", "cz", Channel("PAULI_CHANNEL_2", CZ_PAULI)),
        ("CZ spectator", "spectator", Channel("PAULI_CHANNEL_1",
                                              (5e-4, 5e-4, 1.3e-3))),
        ("CZ loss", "cz_qubit", loss),
        ("measurement", "measure", Channel("X_ERROR", (P_MEASURE,))),
    ]
    if loss_on_spectators:
        model.append(("CZ loss", "spectator", loss))
    if feedforward_noise:
        model.append(("1q gate", "feedforward", d1))
    model = tuple(model)
    return model if p_ph is None else scaled(model, p_ph / combined(model))


def combined(model: Model) -> float:
    """Eq. D1: p_CZ + 2 p_CZ,loss + p_move + p_move,loss."""
    def total(role):
        return sum(c.total for _, r, c in model if r == role)
    return total("cz") + 2 * total("cz_qubit") + total("move")


def scaled(model: Model, s: float) -> Model:
    return tuple((row, role, c.scaled(s)) for row, role, c in model)


def only(model: Model, rows) -> Model:
    """Keep the channels of the named Table II rows, drop the rest."""
    rows = {rows} if isinstance(rows, str) else set(rows)
    unknown = rows - {row for row, _, _ in model}
    if unknown:
        raise ValueError(f"no such rows: {sorted(unknown)}")
    return tuple(entry for entry in model if entry[0] in rows)


@dataclasses.dataclass
class _Op:
    gate: str                     # R RX H CZ R_Z FF M MX
    targets: list                 # qubits; for CZ the flat pair list
    detectors_before: int
    text: str = ""                # R_Z's argument, or FF's original line
    basis: dict = dataclasses.field(default_factory=dict)  # q -> "RX"/"MX"


def _parse(text: str):
    """Split a circuit into header, noisy ops interleaved with pass-through
    lines, and the noiseless tail; noise lines are dropped."""
    off = text.index(_NOISE_OFF)
    body, tail = text[:off], text[off:]
    coords, items, detectors = {}, [], 0
    for line in body.splitlines():
        m = _LINE.match(line.strip())
        name = m.group(1) if m else None
        if name in NOISE_GATES:
            continue
        if name == "QUBIT_COORDS":
            c = _COORDS.match(line.strip())
            coords[int(c.group(2))] = tuple(
                float(x) for x in c.group(1).split(","))
        if name == "DETECTOR":
            detectors += 1
        targets = m.group(4).split() if m else []
        if name in ("R", "RX", "M", "MX") and targets:
            items.append(_Op(name, [int(t) for t in targets], detectors))
        elif name == "CX" and m.group(2) is None:
            qubits = [int(t) for t in targets]
            items.append(_Op("H", qubits[1::2], detectors))
            items.append(_Op("CZ", qubits, detectors))
            items.append(_Op("H", qubits[1::2], detectors))
        elif name == "CX" and m.group(2) == "[FEED_FORWARD]":
            qubits = [int(t) for t in targets if not t.startswith("rec")]
            items.append(_Op("FF", list(dict.fromkeys(qubits)), detectors,
                             text=line.strip()))
        elif name == "R_Z":
            items.append(_Op("R_Z", [int(t) for t in targets], detectors,
                             text=m.group(3)))
        elif name in ("R", "RX", "M", "MX"):
            continue                              # an empty instruction
        else:
            items.append(line)
    return coords, items, tail


def _native(items, minimal: bool):
    """Turn RX/MX into R+H / H+M, then (if minimal) cancel H H pairs and
    fold the remaining H's next to a reset or measurement back in."""
    out = []
    for item in items:
        if isinstance(item, _Op) and item.gate == "RX":
            out += [_Op("R", item.targets, item.detectors_before),
                    _Op("H", list(item.targets), item.detectors_before)]
        elif isinstance(item, _Op) and item.gate == "MX":
            out += [_Op("H", list(item.targets), item.detectors_before),
                    _Op("M", item.targets, item.detectors_before)]
        else:
            out.append(item)
    if not minimal:
        return out
    ops = [item for item in out if isinstance(item, _Op)]

    def history():
        seq = {}
        for op in ops:
            for q in op.targets:
                seq.setdefault(q, []).append(op)
        return seq

    for q, seq in history().items():            # H H -> nothing
        stack = []
        for op in seq:
            if op.gate == "H" and stack and stack[-1].gate == "H":
                stack.pop().targets.remove(q)
                op.targets.remove(q)
            else:
                stack.append(op)
    for q, seq in history().items():            # R H -> RX, H M -> MX
        for a, b in zip(seq, seq[1:]):
            if a.gate == "R" and b.gate == "H" and q in b.targets:
                a.basis[q] = "RX"
                b.targets.remove(q)
            elif a.gate == "H" and b.gate == "M" and q in a.targets:
                b.basis[q] = "MX"
                a.targets.remove(q)
    return out


def _runs(op):
    """An R or M op as consecutive same-basis runs, in target order (so the
    measurement record keeps its order)."""
    runs = []
    for q in op.targets:
        gate = op.basis.get(q, op.gate)
        if runs and runs[-1][0] == gate:
            runs[-1][1].append(q)
        else:
            runs.append((gate, [q]))
    return runs


def renoise(text: str, d: int, model: Model, *, hadamards: str = "minimal",
            mover: str = "ancilla", window: str = "all") -> str:
    """Rebuild a STAR circuit in the native gate set under `model`.

    `mover` is the atom of each CZ pair that is transported to its partner
    ("ancilla" or "data"; App. D c: one atom per pair moves). `window`
    keeps noise only in the "injection" window (up to the last post-selected
    detector), only in the "memory" rounds, or in "all" of the noisy region.
    """
    if hadamards not in ("minimal", "naive"):
        raise ValueError(f"unknown hadamards {hadamards!r}")
    if mover not in ("ancilla", "data"):
        raise ValueError(f"unknown mover {mover!r}")
    if window not in ("all", "injection", "memory"):
        raise ValueError(f"unknown window {window!r}")
    coords, items, tail = _parse(text)
    every = sorted(coords)
    ancilla = {q for q, c in coords.items() if all(x == int(x) for x in c)}
    post = n_postselected(d)
    roles = {role: [c for _, r, c in model if r == role] for role in ROLES}

    def noise(role, targets, basis=None):
        lines = []
        for c in roles[role]:
            if basis == "X" and c.gate == "X_ERROR":
                c = Channel("Z_ERROR", c.args)    # a flip of an X result
            line = c.line(targets)
            if line:
                lines.append(line)
        return lines

    lines = []
    for item in _native(items, hadamards == "minimal"):
        if not isinstance(item, _Op):
            lines.append(item)
            continue
        op = item
        if not op.targets:
            continue
        noisy = (window == "all"
                 or (window == "injection") == (op.detectors_before < post))
        quiet = (lambda role, targets, basis=None: []) if not noisy \
            else noise
        if op.gate in ("R", "M"):
            for gate, qubits in _runs(op):
                basis = "X" if gate.endswith("X") else "Z"
                if op.gate == "M":
                    lines += quiet("measure", qubits, basis)
                lines.append(f"{gate} " + " ".join(map(str, qubits)))
                if op.gate == "R":
                    lines += quiet("init", qubits)
        elif op.gate == "H":
            lines.append("H " + " ".join(map(str, op.targets)))
            lines += quiet("hadamard", op.targets)
        elif op.gate == "CZ":
            pairs = list(zip(op.targets[::2], op.targets[1::2]))
            for a, b in pairs:
                if (a in ancilla) == (b in ancilla):
                    raise ValueError(f"CZ {a} {b} is not ancilla-data")
            movers = [a if (a in ancilla) == (mover == "ancilla") else b
                      for a, b in pairs]
            lines += quiet("move", movers)
            lines.append("CZ " + " ".join(map(str, op.targets)))
            lines += quiet("cz", op.targets)
            lines += quiet("cz_qubit", op.targets)
            busy = set(op.targets)
            lines += quiet("spectator", [q for q in every if q not in busy])
        elif op.gate == "R_Z":
            lines.append(f"R_Z({op.text}) "
                         + " ".join(map(str, op.targets)))
            lines += quiet("gate1", op.targets)
            lines += quiet("idle1", [q for q in every
                                     if q not in op.targets])
        elif op.gate == "FF":
            lines.append(op.text)
            lines += quiet("feedforward", op.targets)
            lines += quiet("idle1", [q for q in every
                                     if q not in op.targets])
    return "\n".join(lines) + "\n" + tail


def hadamard_count(text: str, *, window_detectors: int | None = None) -> int:
    """Single-qubit Hadamard applications in a circuit's noisy region (up to
    the `window_detectors`-th DETECTOR if given) -- the 1q-gate cost the
    CX -> H CZ H rule adds, which Protocol P02 reports."""
    count = detectors = 0
    for line in text[:text.index(_NOISE_OFF)].splitlines():
        if line.startswith("DETECTOR"):
            detectors += 1
        if window_detectors is not None and detectors >= window_detectors:
            break
        if line.startswith("H "):
            count += len(line.split()) - 1
    return count
