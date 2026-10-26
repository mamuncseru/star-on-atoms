"""Verify that every reference in the bibliography exists and says what we
say it says.

Commitment 3 of OUTLINE.md: no claim in this book is stated from memory. That is only real
if the bibliography is checked, so this resolves every DOI against Crossref
and every arXiv ID against the arXiv API, and compares the returned title
with the one in `references.bib`. A wrong DOI usually resolves to a *real*
paper — the wrong one — so existence alone proves nothing; the title
comparison is the part that catches the mistake.

Results are cached in `data/citation-cache.json` with the date they were
verified, so a routine run costs no network at all and CI does not hammer
either service. `--refresh` re-verifies everything.

A routine run tolerates an unreachable registry — arXiv throttles a burst of
requests with HTTP 429, and a guard that fails on someone else's rate limiter
is a guard people learn to ignore. **`--require-all` does not tolerate it**,
and that is what `make release` uses, because the sentence this tool prints
("the book does not ship on an unverified bibliography") has to be true of the
release gate or it should not be printed.

Run:  python tools/check_citations.py
      python tools/check_citations.py --require-all   (release gate)
      python tools/check_citations.py --refresh
      python tools/check_citations.py --offline   (cache only; never fetch)
"""

from __future__ import annotations

import datetime
import difflib
import time
import json
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
BIB = ROOT / "book" / "bib" / "references.bib"
CACHE = ROOT / "data" / "citation-cache.json"

# Crossref asks for a contact address in the User-Agent and gives politer
# service to requests that carry one.
AGENT = "star-book/0.1 (https://github.com/mamuncseru/star-on-atoms; mailto:abdullah18@temple.edu)"

# arXiv's terms of use ask for roughly one request every three seconds, and it
# answers a burst with HTTP 429 rather than data. Crossref is more relaxed but
# also rewards politeness. The cache means this delay is paid once per new
# entry, not on every run.
PAUSE = {"doi": 0.4, "arxiv": 3.2}
_last_fetch = 0.0

ENTRY = re.compile(r"@(\w+)\s*\{\s*([^,]+),(.*?)\n\}", re.S)
FIELD = re.compile(r"(\w+)\s*=\s*\{(.*?)\}\s*,?\s*\n", re.S)

# Below this ratio the returned title is a different paper, not a formatting
# difference. Chosen so that "{\o}" vs "ø" and LaTeX braces never trip it.
TITLE_MATCH_FLOOR = 0.82


def normalise(title: str) -> str:
    text = re.sub(r"[{}\\$]", "", title)
    text = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def parse_bib() -> list[dict]:
    entries = []
    for kind, key, body in ENTRY.findall(BIB.read_text(encoding="utf-8")):
        fields = {name.lower(): value.strip()
                  for name, value in FIELD.findall(body + "\n")}
        fields.update({"_kind": kind, "_key": key.strip()})
        entries.append(fields)
    return entries


def fetch(url: str, kind: str, timeout: int = 20) -> bytes:
    """One polite request, rate-limited per service."""
    global _last_fetch
    wait = PAUSE[kind] - (time.monotonic() - _last_fetch)
    if wait > 0:
        time.sleep(wait)
    request = urllib.request.Request(url, headers={"User-Agent": AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    finally:
        _last_fetch = time.monotonic()


def title_from_doi(doi: str) -> str:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    payload = json.loads(fetch(url, "doi"))
    titles = payload["message"].get("title") or []
    return titles[0] if titles else ""


def title_from_arxiv(eprint: str) -> str:
    identifier = eprint.split("v")[0]
    url = ("http://export.arxiv.org/api/query?id_list="
           + urllib.parse.quote(identifier))
    tree = ET.fromstring(fetch(url, "arxiv"))
    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    node = tree.find("atom:entry/atom:title", namespace)
    return node.text.strip() if node is not None and node.text else ""


def main() -> int:
    refresh = "--refresh" in sys.argv
    offline = "--offline" in sys.argv
    require_all = "--require-all" in sys.argv

    entries = parse_bib()
    if not entries:
        print("references.bib is empty — nothing to check.")
        return 0

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    today = datetime.date.today().isoformat()

    problems, unreachable, verified, cached = [], [], 0, 0

    for entry in entries:
        key = entry["_key"]
        expected = entry.get("title", "")
        identifiers = [("doi", entry["doi"])] if "doi" in entry else []
        if "eprint" in entry:
            identifiers.append(("arxiv", entry["eprint"]))

        if not identifiers:
            problems.append((key, "no DOI and no arXiv ID — unverifiable"))
            continue

        for kind, value in identifiers:
            slot = f"{kind}:{value}"
            if slot in cache and not refresh:
                found = cache[slot]["title"]
                cached += 1
            elif offline:
                unreachable.append((key, slot, "not cached, --offline"))
                continue
            else:
                found, failure = None, None
                for attempt in range(3):
                    try:
                        found = (title_from_doi(value) if kind == "doi"
                                 else title_from_arxiv(value))
                        break
                    except urllib.error.HTTPError as error:
                        failure = f"HTTP {error.code}"
                        if error.code != 429:
                            break
                        time.sleep(5 * (attempt + 1))   # asked to slow down
                    except (urllib.error.URLError, TimeoutError,
                            ET.ParseError, KeyError,
                            json.JSONDecodeError) as error:
                        failure = type(error).__name__
                        break
                if found is None:
                    unreachable.append((key, slot, failure or "no title"))
                    continue
                cache[slot] = {"title": found, "checked": today}
                verified += 1

            if not found:
                problems.append((key, f"{slot} resolves but has no title"))
                continue

            want, got = normalise(expected), normalise(found)
            ratio = difflib.SequenceMatcher(None, want, got).ratio()
            # A registry very often stores the title without its subtitle
            # ("...Information" vs "...Information: 10th Anniversary
            # Edition"), which is a cataloguing difference, not a wrong DOI.
            # One title containing the other from the start is accepted; a
            # merely similar title is not.
            subtitle_only = (len(min(want, got, key=len)) >= 25
                             and (want.startswith(got) or got.startswith(want)))
            if ratio < TITLE_MATCH_FLOOR and not subtitle_only:
                problems.append(
                    (key, f"{slot} resolves to a different paper "
                          f"(match {ratio:.2f})\n"
                          f"        bib:    {expected[:78]}\n"
                          f"        found:  {found[:78]}"))

    CACHE.write_text(json.dumps(cache, indent=1, sort_keys=True) + "\n")

    for key, why in problems:
        print(f"{key}: {why}")
    if unreachable:
        print()
        for key, slot, why in unreachable:
            print(f"  unreachable  {key}  {slot}  ({why})")

    print()
    print(f"{len(entries)} entries: {verified} verified now, {cached} from "
          f"cache, {len(unreachable)} unreachable.")
    if problems:
        print(f"{len(problems)} citation problem(s). A citation that cannot "
              f"be verified does not ship.")
        return 1
    if unreachable:
        if require_all:
            print(f"{len(unreachable)} reference(s) could not be checked. "
                  f"The book does not ship on an unverified bibliography — "
                  f"re-run when the registries answer.")
            return 1
        print("Network trouble, not a citation problem. Re-run when online; "
              "`--require-all` (what `make release` uses) treats this as "
              "fatal.")
        return 0
    print("Every verifiable reference resolves to the paper it claims.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
