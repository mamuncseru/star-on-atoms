"""Register the `star-book` Jupyter kernel, and capture what it contains.

Quarto is told to use the kernel named `star-book` (see book/_quarto.yml). That
pin matters: without it Quarto picks whichever kernelspec it finds first,
which is fragile on a machine with several environments and produces a book
whose outputs came from an interpreter nobody chose.

This registers that name against **the Python currently running this script**,
so the kernel and the environment you tested in cannot diverge. Run it from
inside the environment you intend to build the book with:

    source ~/.venvs/star-book/bin/activate
    python tools/install_kernel.py

It also writes `data/environment-capture.json`: the interpreter, the platform,
and the exact version of every package the book imports. That file is the
evidence behind the book's reproducibility claim, and it is committed, so a
reader can see precisely which stack produced the numbers on the page.

Run:  python tools/install_kernel.py
      python tools/install_kernel.py --check   (report, register nothing)
"""

from __future__ import annotations

import datetime
import importlib.metadata as metadata
import json
import pathlib
import platform
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAPTURE = ROOT / "data" / "environment-capture.json"

NAME = "star-book"
DISPLAY = "STAR on Atoms"

# Everything the book imports, by the part that first needs it. A package
# recorded as `null` is simply not installed yet, which is expected until the
# part that needs it begins.
TRACKED = {
    # tsim is the simulator every STAR number in this book comes from; stim
    # builds the detector error models and PyMatching decodes them.
    "core, needed by every part": ["numpy", "scipy", "matplotlib",
                                   "stim", "pymatching", "bloqade-tsim"],
    "Part III (noise models and instruments)": ["bloqade-circuit",
                                                "cirq-core", "sinter"],
    "tooling": ["jupyter-client", "ipykernel"],
}


def versions() -> dict:
    found = {}
    for group, packages in TRACKED.items():
        found[group] = {}
        for package in packages:
            try:
                found[group][package] = metadata.version(package)
            except metadata.PackageNotFoundError:
                found[group][package] = None
    return found


def capture() -> dict:
    return {
        "captured": datetime.date.today().isoformat(),
        "kernel": NAME,
        "interpreter": sys.executable,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": versions(),
    }


def report(record: dict) -> None:
    print(f"interpreter  {record['interpreter']}")
    print(f"python       {record['python']}")
    print(f"platform     {record['platform']}\n")
    for group, packages in record["packages"].items():
        print(f"  {group}")
        for package, version in packages.items():
            mark = version or "not installed"
            print(f"    {package:16s} {mark}")
    print()

    required = record["packages"]["core, needed by every part"]
    missing = [name for name, version in required.items() if version is None]
    if missing:
        print(f"MISSING from the core stack: {', '.join(missing)}")
    else:
        print("The core stack every part needs is present.")


def install() -> int:
    try:
        from ipykernel import kernelspec
    except ImportError:
        print("ipykernel is not installed in this interpreter, so it cannot "
              "be registered as a kernel.\nInstall it, or run this from the "
              "environment you intend to build with.")
        return 1

    path = kernelspec.install(user=True, kernel_name=NAME,
                              display_name=DISPLAY)
    print(f"registered kernel '{NAME}' -> {path}")
    print(f"           pointing at {sys.executable}")
    return 0


def main() -> int:
    record = capture()
    report(record)

    if "--check" in sys.argv:
        print("\n--check: nothing registered, nothing written.")
        return 0

    status = install()
    CAPTURE.parent.mkdir(parents=True, exist_ok=True)
    CAPTURE.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {CAPTURE.relative_to(ROOT)}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
