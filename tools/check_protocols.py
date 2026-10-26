"""Commitment 1 of OUTLINE.md, enforced: the protocol was committed before the result.

Preregistration is the strongest anti-lie mechanism available to this book
and it costs nothing but discipline. It is also the one commitment that
cannot be checked by reading a file, because a protocol written after the
fact reads exactly like one written before it. Only the commit history knows.

So this guard asks git. For every protocol it reads the artifacts the
protocol names, and compares the protocol's **commit date** against the
`captured` date recorded inside each artifact. A result older than the
protocol describing it is a protocol written to fit a result.

  * a protocol that is not committed at all       -> fail
  * a protocol with uncommitted modifications     -> fail, loudly
  * an artifact captured before its protocol      -> fail
  * a protocol naming an artifact that is missing -> fine, it has not run yet

Run:  python tools/check_protocols.py
"""

from __future__ import annotations

import datetime as _dt
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROTOCOLS = ROOT / "protocols"
RESULTS = ROOT / "data" / "results"

ARTIFACTS = re.compile(r"^-\s*\*\*Artifacts:\*\*\s*(.+)$", re.M)
STATUS = re.compile(r"^-\s*\*\*Status:\*\*\s*(\w+)", re.M)


def git(*args: str) -> str:
    out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                         text=True)
    return out.stdout.strip() if out.returncode == 0 else ""


def committed_date(path: pathlib.Path) -> _dt.date | None:
    """The date this file was first committed, or None if it never was."""
    iso = git("log", "--diff-filter=A", "--format=%cs", "--", str(path))
    line = iso.splitlines()[-1] if iso else ""
    try:
        return _dt.date.fromisoformat(line)
    except ValueError:
        return None


def is_dirty(path: pathlib.Path) -> bool:
    return bool(git("status", "--porcelain", "--", str(path)))


def audit(path: pathlib.Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)
    problems: list[str] = []

    status = (STATUS.search(text) or [None, "DRAFT"])[1]
    names = ARTIFACTS.search(text)
    artifacts = []
    if names:
        artifacts = [n.strip() for n in re.split(r"[,\s]+", names.group(1))
                     if n.strip() and not n.strip().startswith("<")]

    registered = committed_date(path)
    if registered is None:
        problems.append(
            f"{rel}: not committed. A protocol that exists only in the "
            "working tree preregisters nothing — commit it before running "
            "anything it describes.")
        return problems

    if is_dirty(path):
        problems.append(
            f"{rel}: has uncommitted changes. Edits after registration are "
            "deviations and belong in the Deviations section, dated, not in "
            "a silent rewrite of the protocol.")

    for name in artifacts:
        artifact = RESULTS / f"{name}.json"
        if not artifact.exists():
            continue      # registered but not yet run: exactly right
        try:
            captured = _dt.date.fromisoformat(
                json.loads(artifact.read_text(encoding="utf-8"))["captured"])
        except Exception:  # noqa: BLE001 -- a malformed artifact is its own bug
            problems.append(f"{rel}: artifact {name} has no readable "
                            "`captured` date")
            continue
        if captured < registered:
            problems.append(
                f"{rel}: artifact {name} was captured {captured}, but the "
                f"protocol was only committed {registered}.\n"
                "    Commitment 1: the result predates its own protocol, so "
                "the protocol is a description rather than a preregistration.")

    if status == "DRAFT" and artifacts:
        problems.append(
            f"{rel}: still marked DRAFT but names artifacts. Set the status "
            "to COMMITTED before running, so the history records which it "
            "was.")
    return problems


def main() -> int:
    if not PROTOCOLS.exists():
        print("check_protocols: no protocols/ directory yet")
        return 0

    files = [p for p in sorted(PROTOCOLS.glob("*.md"))
             if p.name != "TEMPLATE.md"]
    problems = [p for f in files for p in audit(f)]

    print(f"check_protocols: {len(files)} protocol(s)")
    for problem in problems:
        print(f"  ✗ {problem}")
    if problems:
        print(f"\n{len(problems)} protocol problem(s).")
        return 1
    if not files:
        print("  (none registered yet; P01 must be committed before any run)")
    else:
        print("  ✓ every protocol was committed before its results existed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
