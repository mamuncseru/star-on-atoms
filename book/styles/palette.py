"""The role palette — colour as meaning, not decoration.

Across every chapter five hues mean exactly one thing each, so a reader can
skim any figure and know what is being compared before reading the axes:

    blue    the STAR result under study: a measured logical error, a fitted
            coefficient, the curve this book is about
    slate   the reference it is checked against: QuEra's published curve, a
            paper's number, the uniform-noise baseline — always, nothing else
    amber   a noise channel being varied: the knob in a sensitivity scan
    red     a cost: physical qubits, logical failure, lost simulation volume
    teal    acceptance: the post-selection rate, the shots that survived

The hex values are the series palette shared with the QEC, Qiskit, PennyLane
and QML-Measured volumes, so the books read as one set and the separations
measured for the series hold here unchanged. This book re-reads the roles for
its subject and exports them as `STAR`, `REFERENCE`, `CHANNEL` and `ACCEPT`
so figure code says what it means.

Two rules make the encoding real rather than decorative. **Slate is
reserved**: nothing but a reference or baseline is ever slate. And **colour
is never the sole encoding** — every hue is paired with a marker and a dash
pattern here, so the figures survive greyscale printing and the two
commonest colour-vision deficiencies.

This file is the single source of truth. `theme-light.scss` restates the same
values for the web theme and `verify_scss()` fails if the two drift.
"""

from __future__ import annotations

import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent

# The five hues, drawn from the series' validated figure cycle.
#
# Note that the series' *callout* accents and its *figure* colours are two
# different sets, and mixing them up is a trap: the callout accents are tuned
# to sit behind a tinted header, and two of them fall below 3:1 against the
# figure surface, so they cannot carry data marks. These five come from the
# figure cycle, which is the set validated for that job.
#
# Measured on the series figure surface #fcfcfb, all pairs:
#
#   lightness band      PASS   all five inside L 0.43-0.77
#   CVD separation      PASS   dE 10.4 worst all-pairs (red vs slate, protan)
#   normal-vision floor PASS   dE 20.8 worst
#   contrast            WARN   amber at 2.11:1 against the surface
#
# The amber warning obliges visible labels rather than colour alone. Every
# figure in this book carries them: each mark is directly labelled with its
# value, and each role below owns a marker and a dash pattern too.
QUANTUM = "#2a78d6"     # series blue  — the quantum code; bit-flip (X) sector
CLASSICAL = "#52514e"   # series slate — the classical code or decoder, always
PHASE = "#eda100"       # series amber — the phase-flip (Z) sector
COST = "#e34948"        # series red   — qubits, logical failure, latency
SIGNAL = "#1baf7a"      # series teal  — the syndrome: detection events

# The same roles under the names this book's figures use. The role keys stay
# the series' so the web theme and the sister volumes agree; the aliases let
# figure code say what it means.
STAR = QUANTUM          # the measured STAR quantity under study
REFERENCE = CLASSICAL   # a published curve or baseline it is checked against
CHANNEL = PHASE         # the noise channel being varied
ACCEPT = SIGNAL         # post-selection acceptance

# Dark mode gets its own steps, chosen against the dark surface rather than
# lightened, and matched to theme-dark.scss.
DARK = {
    "quantum": "#3987e5",
    "classical": "#a8a69f",
    "phase": "#c98500",
    "cost": "#e8615f",
    "signal": "#2fbf8b",
}

# Neutrals, matched to the series figure style so a reader moving between the
# books does not feel the ground shift.
INK = "#0b0b0b"         # figure text
MUTED = "#52514e"       # axis labels, annotations
AXIS = "#898781"        # tick marks
GRID = "#e1e0d9"
EDGE = "#c3c2b7"        # axis spines
PAPER = "#fcfcfb"       # the series figure surface

ROLES = {
    "quantum": QUANTUM,
    "classical": CLASSICAL,
    "phase": PHASE,
    "cost": COST,
    "signal": SIGNAL,
}

# Colour is never alone. Each role also owns a marker and a dash pattern.
MARKERS = {"quantum": "o", "classical": "D", "phase": "^",
           "cost": "s", "signal": "v"}
DASHES = {
    "quantum": (None, None),
    "classical": (6, 2),
    "phase": (4, 1.5),
    "cost": (1, 1.5),
    "signal": (3, 1, 1, 1),
}


def colour_for(role: str, mode: str = "light") -> str:
    """The hue for a role name."""
    table = DARK if mode == "dark" else ROLES
    try:
        return table[role]
    except KeyError:
        raise KeyError(
            f"no palette role {role!r}. The palette is deliberately closed: "
            f"a figure needing a sixth colour is usually a figure making a "
            f"sixth kind of comparison, which the book does not have."
        ) from None


def style(role: str, mode: str = "light") -> dict:
    """Full plot style for a role.

    Use this rather than passing `color=` by hand, so no figure in the book
    can accidentally draw a classical algorithm in anything but slate — and
    so the marker and dash pattern always travel with the hue. The secondary
    encoding is not decoration: it is what discharges the contrast warning
    the amber carries against the figure surface.
    """
    return {
        "color": colour_for(role, mode),
        "marker": MARKERS[role],
        "dashes": DASHES[role],
    }


def verify_scss(path: pathlib.Path | None = None) -> list[str]:
    """Check that the web theme still agrees with this file.

    Called by `tools/check_code.py`. A palette that has drifted between the
    figures and the CSS would break the one promise the colour system makes.
    """
    path = path or HERE / "theme-light.scss"
    if not path.exists():
        return [f"{path.name} is missing"]
    text = path.read_text(encoding="utf-8")
    problems = []
    for name, value in (("quantum", QUANTUM), ("classical", CLASSICAL),
                        ("phase", PHASE), ("cost", COST),
                        ("signal", SIGNAL)):
        found = re.search(rf"\$role-{name}:\s*(#[0-9a-fA-F]{{6}})", text)
        if not found:
            problems.append(f"theme-light.scss does not define $role-{name}")
        elif found.group(1).lower() != value.lower():
            problems.append(
                f"theme-light.scss has $role-{name}: {found.group(1)}, "
                f"palette.py has {value} — the figures and the web theme "
                "have drifted apart")
    return problems


def apply() -> None:
    """Install the book's matplotlib style."""
    import matplotlib.pyplot as plt

    plt.style.use(str(HERE / "star.mplstyle"))


__all__ = ["QUANTUM", "CLASSICAL", "PHASE", "COST", "SIGNAL",
           "STAR", "REFERENCE", "CHANNEL", "ACCEPT",
           "INK", "MUTED", "AXIS", "GRID", "EDGE", "PAPER", "DARK",
           "ROLES", "MARKERS", "DASHES", "colour_for", "style", "apply",
           "verify_scss"]
