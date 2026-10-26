"""Compile every equation in the book, exactly as the PDF will.

The book is single-source: the same `.qmd` becomes the website (KaTeX) and the
PDF (Typst, via Pandoc's typst writer). A handful of perfectly valid LaTeX
constructs survive the first path and break the second, because Pandoc emits
Typst without a separator and Typst then re-parses the result:

    $(-1)^{b}\\,\\frac{a}{b}$   ->  `\\(- 1\\)^bthin a / b`  ->  unknown
                                   variable `bthin`

The first version of this file tried to predict that with regular expressions
and got it wrong in both directions: it flagged `$2^n \\times 2^n$`, which is
fine and appears on nearly every page, while the rule it was built from turned
out to depend on details of Pandoc's spacing that are not worth reverse
engineering. Guessing was the mistake. **This runs the real toolchain**: every
math block in the book goes through the same Pandoc and the same Typst binary
that `quarto render` uses, in one batch compile of about a second.

Two silent-corruption patterns remain, because Typst compiles them happily and
renders them wrong. Those are still caught by pattern, and only those:

    $\\|\\psi\\|^2$   ->  `parallel psi parallel^2`, exponent on the closing bar
    $\\tfrac12$      ->  Typst has no \\tfrac and prints the literal name

Run:  python tools/check_math.py
      python tools/check_math.py --list   (show every block it scanned)
"""

from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
BOOK = ROOT / "book"

# Fenced code blocks are not maths and must not be scanned; a Python string
# containing "$" is not a typesetting problem.
FENCE = re.compile(r"^```.*?^```", re.M | re.S)

DISPLAY = re.compile(r"\$\$(.+?)\$\$", re.S)
INLINE = re.compile(r"(?<!\$)\$(?!\$)([^$\n]+?)\$(?!\$)")

MARKER = "STARMATHBLOCK"

# Constructs Typst accepts and renders incorrectly. The compiler cannot catch
# these, so they stay as patterns — and the list stays this short on purpose.
# Two kinds of silent corruption, caught two different ways.
#
# SOURCE rules look at the LaTeX. They are for constructs with no legitimate
# use in this book, where the source alone is decisive.
SILENT_SOURCE = [
    (
        "ascii-norm",
        re.compile(r"\\\|"),
        "use \\lVert and \\rVert; with \\| the exponent lands on the "
        "closing bar instead of the norm",
    ),
    (
        "tfrac-dfrac",
        re.compile(r"\\[td]frac"),
        "use \\frac; Typst has no \\tfrac or \\dfrac and prints the "
        "literal macro name",
    ),
]

# EMITTED rules look at the Typst that Pandoc actually produced. This is the
# only way to be right about them, and finding that out cost two rewrites of
# this file. Whether `^{b}\left(x\right)` is safe depends on whether Pandoc
# emits `^b(x)` or `^b (x)`, and that in turn depends on what the parenthesis
# contains -- `$\log^{c}\left(1/\varepsilon\right)$` is fine while
# `$(-1)^{b}\left(a-c\right)$` silently lifts the whole bracket into the
# exponent. Predicting it from the LaTeX is not worth doing; reading the
# output is exact.
SILENT_EMITTED = [
    (
        "script-swallows-group",
        # `^b(` with an UNESCAPED paren: Typst reads it as a call and pulls
        # the bracket into the exponent. Pandoc escapes plain `(` as `\(`,
        # which is safe; `\left(` is what produces the bare one.
        re.compile(r"[\^_][A-Za-z0-9]\("),
        "Typst reads this as a call and lifts the bracket into the exponent. "
        "Reorder so the script comes last, or drop \\left ... \\right",
    ),
    (
        "glued-command",
        # Pandoc drops the space after an escaped `)`, so a superscripted
        # command whose base ends in a bracket runs into whatever follows:
        # `S(x)^\dagger W` emits `S\(x\)^daggerW`, and Typst rejects the
        # identifier `daggerW`. Found in the sister volume's Ch. 23.
        re.compile(r"(?:\^|_)[a-z]{2,}[A-Z]"),
        "a script command has absorbed the next symbol -- Pandoc drops the "
        "space after a `)` in the base. Name the operator instead: write "
        "V = W_2 S(x) W_1, then V^\\dagger",
    ),
    (
        "negative-space",
        # `\!` becomes #h(-1em), a full em rather than a thin space, which
        # overlaps the neighbouring glyphs.
        re.compile(r"#h\(-1em\)"),
        "delete the \\! -- Pandoc renders it as a full negative em and the "
        "glyphs collide",
    ),
]


emitted: dict = {}


def split_by_marker(typ: str) -> dict:
    """The emitted Typst for each block, keyed by its index."""
    pieces, current, buffer = {}, None, []
    for line in typ.splitlines():
        found = re.search(rf"{MARKER}(\d{{5}})", line)
        if found:
            if current is not None:
                pieces[current] = "\n".join(buffer)
            current, buffer = int(found.group(1)), []
        elif current is not None:
            buffer.append(line)
    if current is not None:
        pieces[current] = "\n".join(buffer)
    return pieces


def find_tool(name: str) -> str | None:
    """Pandoc and Typst as shipped inside Quarto, or on PATH."""
    found = shutil.which(name)
    if found:
        return found
    roots = [pathlib.Path.home() / "opt"]
    quarto = shutil.which("quarto")
    if quarto:
        roots.append(pathlib.Path(quarto).resolve().parent.parent)
    for root in roots:
        for candidate in sorted(root.glob(f"**/tools/*/{name}")):
            if candidate.is_file():
                return str(candidate)
    return None


def sources() -> list[pathlib.Path]:
    found = sorted(BOOK.glob("chapters/part*/ch*.qmd"))
    found += sorted(BOOK.glob("appendices/*.qmd"))
    found += [BOOK / "index.qmd"]
    return [path for path in found if path.exists()]


def math_blocks(text: str):
    """(line number, source, is_display) for every math block."""
    stripped = FENCE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    for pattern, display in ((DISPLAY, True), (INLINE, False)):
        for match in pattern.finditer(stripped):
            line = stripped.count("\n", 0, match.start()) + 1
            yield line, match.group(1), display


def collect():
    blocks = []
    for path in sources():
        text = path.read_text(encoding="utf-8")
        for line, body, display in math_blocks(text):
            blocks.append({"path": path.relative_to(ROOT), "line": line,
                           "body": body, "display": display})
    return blocks


def compile_all(blocks, pandoc: str, typst: str) -> list[tuple[int, str]]:
    """Run the real toolchain. Returns (block index, message) for failures.

    Typst stops at the first error in a document, so one compile finds one
    bad block. Each failure is replaced by a trivially valid expression and
    the batch is compiled again, which converges on the full set in as many
    passes as there are broken equations — normally zero, and a second or so
    per pass when there is work to do.
    """
    bodies = [block["body"].strip() for block in blocks]
    failures, guard = [], 0
    while guard <= len(blocks):
        guard += 1
        found = compile_once(blocks, bodies, pandoc, typst)
        if not found:
            break
        for index, message in found:
            if index < 0:
                return found
            failures.append((index, message))
            bodies[index] = "x"          # neutralise and look for the next
    return failures


def compile_once(blocks, bodies, pandoc: str, typst: str):
    """One pass of the real toolchain over the current bodies."""
    document = []
    for index, block in enumerate(blocks):
        document.append(f"{MARKER}{index:05d}\n")
        body = bodies[index]
        document.append(f"$$\n{body}\n$$\n" if block["display"]
                        else f"${body}$\n")

    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        (work / "blocks.md").write_text("\n".join(document), encoding="utf-8")
        converted = subprocess.run(
            [pandoc, "-f", "markdown", "-t", "typst", str(work / "blocks.md")],
            capture_output=True, text=True)
        if converted.returncode != 0:
            return [(-1, f"pandoc failed: {converted.stderr.strip()}")]

        typ = ("#set page(width: 16cm, height: auto, margin: 8pt)\n"
               + converted.stdout)
        emitted.clear()
        emitted.update(split_by_marker(typ))
        (work / "blocks.typ").write_text(typ, encoding="utf-8")
        compiled = subprocess.run(
            [typst, "compile", str(work / "blocks.typ"),
             str(work / "blocks.pdf")],
            capture_output=True, text=True)
        if compiled.returncode == 0:
            return []

        lines = typ.splitlines()
        failures, seen = [], set()
        for report in re.finditer(r"blocks\.typ:(\d+):", compiled.stderr):
            at = int(report.group(1)) - 1
            index = None
            for back in range(at, -1, -1):
                found = re.search(rf"{MARKER}(\d{{5}})", lines[back])
                if found:
                    index = int(found.group(1))
                    break
            detail = lines[at].strip() if 0 <= at < len(lines) else ""
            if index is not None and index not in seen:
                seen.add(index)
                failures.append((index, f"Typst rejects: {detail[:90]}"))
        if not failures:
            failures.append((-1, compiled.stderr.strip()[:400]))
        return failures


def main() -> int:
    blocks = collect()
    if not blocks:
        print("No maths found — nothing to check.")
        return 0

    if "--list" in sys.argv:
        for block in blocks:
            print(f"  {block['path']}:{block['line']}  "
                  f"{block['body'].strip()[:66]}")

    problems = []
    for block in blocks:
        for name, pattern, advice in SILENT_SOURCE:
            if pattern.search(block["body"]):
                problems.append((block, name, advice))

    pandoc, typst = find_tool("pandoc"), find_tool("typst")
    if pandoc and typst:
        for index, message in compile_all(blocks, pandoc, typst):
            if index < 0:
                print(f"toolchain: {message}")
                return 1
            problems.append((blocks[index], "typst-error", message))
        for index, produced in emitted.items():
            for name, pattern, advice in SILENT_EMITTED:
                if pattern.search(produced):
                    problems.append((blocks[index], name, advice))
        checked = "compiled and inspected through Pandoc + Typst"
    else:
        checked = ("pandoc/typst not found — pattern checks only, the PDF "
                   "build remains the real guard")

    for block, name, detail in problems:
        print(f"{block['path']}:{block['line']}: [{name}] "
              f"{block['body'].strip()[:70]}")
        print(f"    -> {detail}")

    print()
    if problems:
        print(f"{len(problems)} of {len(blocks)} math block(s) will not "
              f"render correctly in the PDF.")
        print("The PDF is half the book. Fix these before shipping.")
        return 1

    print(f"{len(blocks)} math block(s) in {len(sources())} file(s): "
          f"{checked} — all clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
