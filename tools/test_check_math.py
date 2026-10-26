"""Regression tests for tools/check_math.py.

MUST_FAIL holds constructs that actually broke a Typst build of this book.
MUST_PASS holds ones that compiled fine and that an over-eager checker would
flag — the first, regex-based version of check_math.py flagged four of them,
including `$2^n \\times 2^n$`, which appears on nearly every page.

Both lists are run through the real path: Pandoc's typst writer and the Typst
binary, plus the two silent-corruption patterns. If the toolchain is not
available the compiled cases are skipped and said to be skipped, rather than
being quietly reported as passing.

Run:  python tools/test_check_math.py
"""

import importlib.util
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

MUST_FAIL = [
    (r"(-1)^{b}\,\frac{|0\rangle - |1\rangle}{\sqrt{2}}", True),
    (r"(-1)^{b}\cdot\frac{a}{b}", True),
    # Compiles, renders wrong: \left( emits a bare paren that Typst reads as
    # a call, lifting the whole bracket into the exponent.
    (r"\frac{(-1)^{b}\left(a - c\right)}{\sqrt{2}}", True),
    # Compiles, renders wrong: \! becomes a full negative em and the glyphs
    # collide.
    (r"O\!\left(n^2\right)", True),
    # Compiles to an invalid identifier: Pandoc drops the space after the
    # escaped `)`, so the superscripted command runs into the next symbol.
    (r"\langle 0 | S(x)^\dagger M S(x) | 0 \rangle", True),
    (r"\|U\psi\|^2 = \|\psi\|^2", False),
    (r"\tfrac12(+,-,+,-)", False),
]

MUST_PASS = [
    r"2^n \times 2^n",
    r"\sum_x \left| \tilde{\psi}_x \right|^2",
    r"x^{f(x)} + e^{i(\pi - \delta)}",
    r"H^{\otimes n}\psi",
    r"\psi \mapsto U_T \cdots U_2 U_1 \psi",
    r"\lVert \psi \rVert^2 \quad\Longleftrightarrow\quad U^\dagger U = I",
    r"m = O\left(\frac{1}{\varepsilon^{2}}\log\frac{1}{\delta}\right)",
    r"\frac{|0\rangle - |1\rangle}{\sqrt{2}} \times (-1)^{b}",
    r"M = \sum_k \lambda_k \lvert v_k \rangle \langle v_k \rvert = V \Lambda V^\dagger",
    # A dagger with no bracket in the base keeps its space, so the
    # glued-command rule must not fire here.
    r"V_\theta^\dagger M V_\theta",
    # Plain parentheses are escaped by Pandoc, so these are safe even though
    # a source-level pattern would flag them. Both appear in the book.
    r"\frac{1}{2}\sum_x (-1)^{f(x)} \lvert x \rangle",
    r"x^{c}(y + z)",
    r"\log^{c}\left(1/\varepsilon\right)",
]

def load():
    spec = importlib.util.spec_from_file_location(
        "check_math", HERE / "check_math.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    check = load()
    pandoc, typst = check.find_tool("pandoc"), check.find_tool("typst")
    have_toolchain = bool(pandoc and typst)

    def silent_hits(body):
        return [name for name, pattern, _ in check.SILENT_SOURCE
                if pattern.search(body)]

    def compiler_hits(bodies):
        if not have_toolchain:
            return set()
        blocks = [{"body": body, "display": False} for body in bodies]
        bad = {index for index, _ in check.compile_all(blocks, pandoc, typst)}
        # compile_all leaves the emitted Typst behind; the silent-corruption
        # rules are patterns over that, not over the LaTeX.
        for index, produced in check.emitted.items():
            for _, pattern, _advice in check.SILENT_EMITTED:
                if pattern.search(produced):
                    bad.add(index)
        return bad

    all_bodies = [body for body, _ in MUST_FAIL] + list(MUST_PASS)
    rejected = compiler_hits(all_bodies)

    failures = 0
    for index, (body, needs_compiler) in enumerate(MUST_FAIL):
        caught = bool(silent_hits(body)) or index in rejected
        if needs_compiler and not have_toolchain:
            print(f"  skip    {body[:52]:54s} (no toolchain)")
            continue
        print(f"  {'caught ' if caught else 'MISSED '} {body[:52]:54s}")
        failures += not caught

    offset = len(MUST_FAIL)
    for index, body in enumerate(MUST_PASS):
        flagged = bool(silent_hits(body)) or (offset + index) in rejected
        print(f"  {'ok     ' if not flagged else 'FALSE+ '} {body[:52]:54s}")
        failures += flagged

    print()
    if not have_toolchain:
        print("Pandoc/Typst not found: compiled cases were skipped.")
    if failures:
        print(f"{failures} regression failure(s).")
        return 1
    print(f"All {len(MUST_FAIL)} known-bad and {len(MUST_PASS)} known-good "
          f"constructs classified correctly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
