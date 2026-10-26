"""Three guards on the code the book ships.

1. **Line length in chapter code cells.** The PDF sets code at 9pt across a
   14.6 cm measure, which fits 76 characters. A longer line wraps, and a
   wrapped line in a printed listing is a line the reader mistrusts. Chapter
   sources are checked, not just `code/`, because the chapter is the source
   the scripts are generated from.

2. **The palette has not drifted.** `book/styles/palette.py` is the single
   source of truth for the five role colours; `theme-light.scss` restates
   them for the web. If they disagree, the figures and the site are making
   different claims with the same hue.

3. **Every companion script still runs**, with deprecation warnings escalated
   to errors. The book renders with warnings suppressed so readers get clean
   output, which means a deprecated API would otherwise pass silently into
   print. Failures are attributed by traceback: a warning raised inside a
   library the book teaches (NumPy, stim, PyMatching) fails the build; one
   from an unrelated dependency is reported but not fatal.

4. **Every printed line fits the measure too.** A cell's output is set in the
   same 9pt monospace as its code, so an 88-character table header wraps just
   as an 88-character source line does. The generated figure scripts execute
   every cell of their chapter, so their stdout is checked against the same
   limit. Added when Part I's first render wrapped about twenty output lines
   that the source-line check could not see.

Run:  python tools/check_code.py
      python tools/check_code.py --strict   (fail on third-party ones too)
"""

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_LINE = 76

CELL = re.compile(r"```\{python\}\n(.*?)```", re.S)

# Libraries the book teaches. A deprecation raised from inside one of these
# is a promise the book is about to break in print.
TAUGHT = ("numpy", "scipy", "stim", "pymatching", "sinter", "tsim",
          "bloqade", "cirq", "starlab", "matplotlib")

WRAPPER = """
import sys, runpy, warnings

warnings.simplefilter("error", DeprecationWarning)
warnings.simplefilter("error", PendingDeprecationWarning)
warnings.simplefilter("error", FutureWarning)

# Present the script with its own name and NO extra arguments, exactly as if
# the reader had run it directly. Leaving the path in argv[1] makes every
# argparse-based script fail with "unrecognized arguments".
path = sys.argv[1]
sys.argv = [path]

runpy.run_path(path, run_name="__main__")
"""

WARNING_CLASSES = ("DeprecationWarning", "PendingDeprecationWarning",
                   "FutureWarning")


def check_line_length() -> list[tuple[pathlib.Path, int, int]]:
    """Over-long lines inside chapter code cells."""
    long_lines = []
    for path in sorted(ROOT.glob("book/**/*.qmd")):
        text = path.read_text(encoding="utf-8")
        for cell in CELL.finditer(text):
            offset = text.count("\n", 0, cell.start(1)) + 1
            for number, line in enumerate(cell.group(1).splitlines()):
                # `#|` cell directives are Quarto metadata, not printed code:
                # a long fig-cap is a caption, and captions wrap on purpose.
                if line.lstrip().startswith("#|"):
                    continue
                if len(line) > MAX_LINE:
                    long_lines.append(
                        (path.relative_to(ROOT), offset + number, len(line)))
    return long_lines


def check_palette() -> list[str]:
    sys.path.insert(0, str(ROOT / "book" / "styles"))
    import palette                                          # noqa: E402
    return palette.verify_scss()


def final_exception(traceback_text: str) -> str:
    lines = [line for line in traceback_text.strip().splitlines()
             if line.strip()]
    return lines[-1].split(":", 1)[0].strip() if lines else ""


def is_deprecation(traceback_text: str) -> bool:
    return final_exception(traceback_text).endswith(WARNING_CLASSES)


def blames_taught_library(traceback_text: str) -> bool:
    """Did the escalated warning come from a library the book teaches?

    Frames under the repository root are our own code, not the library's, and
    are discarded before looking — otherwise a traceback that merely mentions
    a book file named `numpy_intro.py` would blame NumPy for our bug.
    """
    root = str(ROOT)
    foreign = [line for line in traceback_text.splitlines() if root not in line]
    return any(name in line.lower() for line in foreign for name in TAUGHT)


def run_scripts(strict: bool) -> int:
    scripts = sorted(ROOT.glob("code/**/*.py"))
    if not scripts:
        print("No scripts under code/ yet — nothing to run.")
        return 0

    deprecated, third_party, broken, wide = [], [], [], []
    for script in scripts:
        rel = script.relative_to(ROOT)
        result = subprocess.run([sys.executable, "-c", WRAPPER, str(script)],
                                capture_output=True, text=True)
        stderr = result.stderr.strip()
        if result.returncode == 0:
            print(f"  ok        {rel}")
            # The generated figure scripts run every cell of a chapter, so
            # their stdout is exactly the output the book prints.
            wide.extend((rel, line) for line in result.stdout.splitlines()
                        if len(line) > MAX_LINE)
        elif not is_deprecation(stderr):
            print(f"  BROKEN    {rel}")
            broken.append((rel, stderr))
        elif blames_taught_library(stderr):
            print(f"  DEPRECATED {rel}")
            deprecated.append((rel, stderr))
        else:
            print(f"  other     {rel}")
            third_party.append((rel, stderr))

    if third_party:
        print(f"\n{len(third_party)} script(s) hit a deprecation in an "
              f"unrelated dependency (reported, not fatal):")
        for rel, err in third_party:
            print(f"  - {rel}: {err.splitlines()[-1][:110]}")

    for label, group in (("BROKEN", broken), ("DEPRECATED", deprecated)):
        for rel, err in group:
            print(f"\n--- {label}  {rel} ---")
            print(err[-2000:])

    if broken or deprecated:
        print(f"\nOf {len(scripts)} script(s): {len(broken)} do not run, "
              f"{len(deprecated)} use a deprecated API the book teaches.")
        return 1
    if wide:
        print()
        for rel, line in wide:
            print(f"  {rel}: prints {len(line)} chars: {line[:56]}...")
        print(f"\n{len(wide)} printed line(s) wider than {MAX_LINE} "
              f"characters. Cell output wraps in the PDF exactly as code "
              f"does.")
        return 1
    if third_party and strict:
        print("\n--strict: failing on third-party deprecations too.")
        return 1
    print(f"\nAll {len(scripts)} script(s) ran clean.")
    return 0


def main() -> int:
    status = 0

    long_lines = check_line_length()
    for rel, line, width in long_lines:
        print(f"{rel}:{line}: code line is {width} chars, limit {MAX_LINE}")
    if long_lines:
        print(f"{len(long_lines)} over-long code line(s) — they wrap in the "
              f"PDF.\n")
        status = 1
    else:
        print(f"Code cells: every line within {MAX_LINE} characters.")

    drift = check_palette()
    for message in drift:
        print(message)
    if drift:
        status = 1
    else:
        print("Palette: palette.py and theme-light.scss agree.")

    print()
    return run_scripts("--strict" in sys.argv) or status


if __name__ == "__main__":
    raise SystemExit(main())
