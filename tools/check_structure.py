"""Every chapter keeps the same contract. This checks that it does.

This book has two jobs: to run one experiment honestly, and to leave its
author able to defend every line of it without notes. The recurring elements
below are the second job made mechanical, because a promise that holds in
Chapter 2 and lapses in Chapter 9 is worse than one never made:

  🎯 Learning Goals   exactly one, opening the chapter
  🧑‍🏫 Whiteboard      at least one: a derivation to reproduce at a board,
                      with no notes and no agent
  🤖 Agent Log        exactly one: what an agent did, what was verified by
                      hand, and what the agent got wrong
  🎤 Interview Drill  at least one box, at least three numbered questions
  💪 Exercises        one callout, at least four numbered items
  🔬 Evidence         at least one in every Part IV chapter, where the
                      experiment lives: a measured number with its provenance

The crash course (Part II) is written for a reader starting from very
little, against an interview in two weeks, so its chapters owe two more:

  ⏱️ 60-Second Answer at least one: what to say, out loud, when asked
  Model answers       a `## Model answers` section answering the drill

Whiteboard, Exercises and Evidence may be waived by a chapter that
genuinely has none, with the reason recorded in the source:

    <!-- no-whiteboard: this chapter is a protocol; nothing to derive -->

Waivers are printed on every run. A silent lapse is the failure mode this
tool exists to prevent; a considered exemption is not.

Run:  python tools/check_structure.py
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Parts whose chapters report measurements and must carry Evidence.
EVIDENCE_PARTS = {"part4"}

# The crash course: chapters must also carry a 60-second answer and model
# answers to their drill.
CRASH_PARTS = {"part2"}

LEARNING = re.compile(r'\{\.callout-note\s+title="🎯')
WHITEBOARD = re.compile(r'\{[^}]*\.whiteboard[^}]*\}')
AGENTLOG = re.compile(r'\{[^}]*\.agentlog[^}]*\}')
DRILL = re.compile(r'\{[^}]*\.drill[^}]*\}')
EVIDENCE = re.compile(r'\{[^}]*\.evidence[^}]*\}')
SIXTY = re.compile(r'\{[^}]*\.sixty[^}]*\}')
MODEL_ANSWERS = re.compile(r"^## Model answers", re.M)
EXERCISES = re.compile(r'\{\.callout-caution\s+title="💪')
NUMBERED = re.compile(r"^\s*(\d+)\.\s+\*\*", re.M)

WAIVER = re.compile(r"<!--\s*no-(whiteboard|exercises|evidence):\s*"
                    r"(.+?)\s*-->", re.S)

MIN_EXERCISES = 4
MIN_DRILL_QUESTIONS = 3

FENCE_OPEN = re.compile(r"^::: *\{")
FENCE_CLOSE = re.compile(r"^:::+\s*$")


def unbalanced_fence(text: str):
    """The line where a ::: div was opened and never closed.

    An unclosed div is invisible on the web -- the browser closes it at the
    end of the page -- and in the PDF it swallows everything after it,
    including the next part opener, which Typst then refuses to paginate.
    Found the hard way in a sister volume; checked here in milliseconds.
    """
    depth, opened_at = 0, None
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if FENCE_OPEN.match(stripped):
            if depth == 0:
                opened_at = (number, stripped[:60])
            depth += 1
        elif FENCE_CLOSE.match(stripped) and depth:
            depth -= 1
    return opened_at if depth else None


# A Typst callout cannot hold a table taller than a page: it renders as
# nothing. Chapter boxes run to about twenty rows.
CALLOUT_TABLE_LIMIT = 40

TEMPLATE = ROOT / "book" / "styles" / "typst-show.typ"


def callouts_can_break() -> bool:
    """Does the PDF template still let a callout break across pages?

    Quarto's stock Typst callout is unbreakable, and a callout taller than
    the space left on its page overprints its own last rows, silently and
    only in the PDF. book/styles/typst-show.typ redefines it; this confirms
    the override is still there.
    """
    if not TEMPLATE.exists():
        return False
    text = TEMPLATE.read_text(encoding="utf-8")
    figure_rule = "#show figure: set block(breakable: true)" in text
    callout_rule = re.search(r"#let callout\(.*?breakable:\s*true", text,
                             re.S)
    return figure_rule and callout_rule is not None


def oversized_callout_table(text: str):
    """A callout holding more table rows than a PDF page can hold."""
    depth, rows, opened_at = 0, 0, None
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if FENCE_OPEN.match(stripped):
            if depth == 0:
                rows, opened_at = 0, (number, stripped[:60])
            depth += 1
        elif FENCE_CLOSE.match(stripped) and depth:
            depth -= 1
            if depth == 0 and rows > CALLOUT_TABLE_LIMIT:
                return opened_at + (rows,)
        elif depth and stripped.startswith("|"):
            rows += 1
    return None


def numbered_in(text: str, opener: re.Pattern) -> int:
    """Numbered items inside every box the opener matches, summed."""
    total = 0
    for start in opener.finditer(text):
        body = text[start.end():]
        end = re.search(r"^:::+\s*$", body, re.M)
        total += len(NUMBERED.findall(body[:end.start()] if end else body))
    return total


def main() -> int:
    chapters = sorted(ROOT.glob("book/chapters/part*/ch*.qmd"))
    if not chapters:
        print("No chapters yet — nothing to check.")
        return 0

    problems, waived = [], []

    if not callouts_can_break():
        problems.append((TEMPLATE.relative_to(ROOT),
                         "callouts can no longer break across pages; a "
                         "tall box will overprint its last rows in the PDF"))

    for path in sorted(ROOT.glob("book/appendices/*.qmd")):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        dangling = unbalanced_fence(text)
        if dangling:
            problems.append((rel, f"unclosed ::: div opened at line "
                                  f"{dangling[0]}: {dangling[1]}"))
        oversized = oversized_callout_table(text)
        if oversized:
            problems.append((rel, f"callout at line {oversized[0]} holds "
                                  f"{oversized[2]} table rows; it will "
                                  f"render as nothing in the PDF"))

    for path in chapters:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        part = path.parent.name
        waivers = {kind: why for kind, why in WAIVER.findall(text)}

        oversized = oversized_callout_table(text)
        if oversized:
            problems.append((rel, f"callout at line {oversized[0]} holds "
                                  f"{oversized[2]} table rows; it will "
                                  f"render as nothing in the PDF"))
        dangling = unbalanced_fence(text)
        if dangling:
            problems.append((rel, f"unclosed ::: div opened at line "
                                  f"{dangling[0]}: {dangling[1]}"))

        goals = len(LEARNING.findall(text))
        if goals != 1:
            problems.append((rel, f"{goals} 🎯 Learning Goals boxes, want 1"))

        logs = len(AGENTLOG.findall(text))
        if logs != 1:
            problems.append((rel, f"{logs} 🤖 Agent Log boxes, want 1"))

        if not DRILL.search(text):
            problems.append((rel, "no 🎤 Interview Drill box"))
        elif numbered_in(text, DRILL) < MIN_DRILL_QUESTIONS:
            problems.append((rel, f"🎤 Interview Drill has fewer than "
                                  f"{MIN_DRILL_QUESTIONS} numbered "
                                  f"questions"))

        checks = [("whiteboard", WHITEBOARD, "🧑‍🏫 Whiteboard", True)]
        checks.append(("evidence", EVIDENCE, "🔬 Evidence",
                       part in EVIDENCE_PARTS))
        for kind, pattern, label, required in checks:
            if not required or pattern.search(text):
                continue
            if kind in waivers:
                waived.append((rel, label, waivers[kind]))
            else:
                problems.append((rel, f"no {label} box"))

        if part in CRASH_PARTS:
            if not SIXTY.search(text):
                problems.append((rel, "no ⏱️ 60-Second Answer box"))
            if not MODEL_ANSWERS.search(text):
                problems.append((rel, "no '## Model answers' section"))

        count = numbered_in(text, EXERCISES)
        if count < MIN_EXERCISES:
            if "exercises" in waivers:
                waived.append((rel, "💪 Exercises", waivers["exercises"]))
            else:
                problems.append(
                    (rel, f"{count} exercises, want at least "
                          f"{MIN_EXERCISES}"))

    for rel, why in problems:
        print(f"{rel}: {why}")

    if waived:
        print()
        for rel, label, why in waived:
            print(f"  waived  {rel}  {label}: {why}")

    print()
    if problems:
        print(f"{len(problems)} structural lapse(s) across "
              f"{len(chapters)} chapter(s).")
        return 1
    print(f"All {len(chapters)} chapter(s) keep the contract"
          + (f" ({len(waived)} considered waiver(s))." if waived else "."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
