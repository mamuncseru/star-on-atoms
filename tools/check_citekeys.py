"""Every \\@key cited in the book must exist in references.bib.

Typst catches a missing key -- but only at the end of a multi-minute render,
after every chapter has been executed. This catches it in milliseconds, which
is the same argument that produced tools/check_math.py.

It also reports entries in the bibliography that nothing cites. Those are not
an error (a reference may be added before the chapter that uses it), but an
uncited entry is usually either a citation that got renamed or a chapter that
was meant to lean on it and does not.

Run:  python tools/check_citekeys.py
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BIB = ROOT / "book" / "bib" / "references.bib"

FENCE = re.compile(r"^```.*?^```", re.M | re.S)
INLINE_CODE = re.compile(r"`[^`\n]*`")
# @key, [@key], [-@key], [@a; @b] -- but not an email address or a decorator.
CITATION = re.compile(r"(?<![\w@.])-?@([A-Za-z][\w:.#$%&+?<>~/-]*)")

# Quarto cross-references share the @ syntax and are not citations:
# @fig-something, @sec-something, @tbl-, @eq-, and the rest.
CROSSREF = re.compile(r"^(fig|sec|tbl|eq|lst|thm|lem|cor|prp|def|exm|exr)-")

DEFINED = re.compile(r"^@\w+\s*\{\s*([^,]+),", re.M)


def sources():
    found = sorted(ROOT.glob("book/chapters/part*/ch*.qmd"))
    found += sorted(ROOT.glob("book/appendices/*.qmd"))
    found += [ROOT / "book" / "index.qmd"]
    return [p for p in found if p.exists()]


def main() -> int:
    defined = set(DEFINED.findall(BIB.read_text(encoding="utf-8")))

    cited, missing = set(), []
    for path in sources():
        text = path.read_text(encoding="utf-8")
        prose = INLINE_CODE.sub(" ", FENCE.sub(" ", text))
        for match in CITATION.finditer(prose):
            key = match.group(1).rstrip(".,;:")
            if CROSSREF.match(key):
                continue                      # a cross-reference, not a cite
            cited.add(key)
            if key not in defined:
                line = prose.count("\n", 0, match.start()) + 1
                missing.append((path.relative_to(ROOT), line, key))

    for path, line, key in missing:
        print(f"{path}:{line}: cites @{key}, which is not in references.bib")

    unused = sorted(defined - cited)
    if unused:
        print(f"\n  {len(unused)} bibliography entr(ies) cited by nothing yet: "
              f"{', '.join(unused)}")

    print()
    if missing:
        print(f"{len(missing)} missing citation key(s). Typst would catch "
              f"these at the end of a full render; this catches them now.")
        return 1
    print(f"All {len(cited)} citation key(s) used in the book are defined.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
