"""MkDocs build hooks, registered under `hooks:` in mkdocs.yml.

1. **The home page is assembled from PROGRESS.md.** Its "Now" section, its
   milestone table (drawn as a timeline) and its newest log entries replace
   the `<!-- progress:... -->` markers in docs/index.md, and the newest
   entry's date becomes "last update". PROGRESS.md is the only file to edit
   when the project moves, so the front page cannot fall behind the log.

2. **Links to files outside the site go to GitHub.** OUTLINE, LEDGER, the
   protocols and the README are the repository's own files, symlinked into
   docs/. Their links to code, results and chapter sources are right on
   GitHub but would 404 on the site; they are pointed at the file on GitHub
   instead.
"""

from __future__ import annotations

import functools
import html
import pathlib
import posixpath
import re
import subprocess

REPO = "https://github.com/mamuncseru/star-on-atoms"
ROOT = pathlib.Path(__file__).resolve().parent.parent
LATEST = 3
STATUS = {"✅": ("done", "done"), "🚧": ("now", "in progress"),
          "⬜": ("next", "next")}
# Pages whose source is a repo file under another name.
SOURCE = {"about.md": "README.md"}

_LINK = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)\)")


def _sections(text: str) -> dict[str, str]:
    out, name = {}, None
    for line in text.splitlines():
        heading = re.match(r"^## (.+?)\s*$", line)
        if heading:
            name = heading.group(1)
            out[name] = []
        elif name:
            out[name].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def _inline(text: str) -> str:
    """The little markdown a milestone may carry, as HTML."""
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", text)


def _timeline(table: str) -> str:
    items = []
    for row in table.splitlines():
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) != 3 or not re.match(r"\d{4}-\d{2}-\d{2}", cells[0]):
            continue
        date, what, mark = cells
        status, label = STATUS[mark]
        pill = (f' <span class="soa-pill">{label}</span>'
                if status == "now" else "")
        items.append(
            f'<li class="soa-{status}"><span class="soa-date">{date}</span>'
            f'<span class="soa-dot" aria-hidden="true"></span>'
            f'<span class="soa-what"><span class="sr-only">{label}: </span>'
            f'{_inline(what)}{pill}</span></li>')
    legend = ('<p class="soa-legend"><span class="soa-key soa-done">done'
              '</span><span class="soa-key soa-now">in progress</span>'
              '<span class="soa-key soa-next">next</span></p>')
    return f'<ol class="soa-timeline">\n' + "\n".join(items) + \
        "\n</ol>\n" + legend


def _home(markdown: str) -> str:
    progress = (ROOT / "PROGRESS.md").read_text(encoding="utf-8")
    parts = _sections(progress)
    entries = [e.strip() for e in re.split(r"(?m)^(?=### )", parts["Log"])
               if e.startswith("### ")]
    updated = re.search(r"\d{4}-\d{2}-\d{2}", entries[0]).group(0)
    now = ('<div class="soa-status" markdown>\n'
           f'<p class="soa-label">As of {updated}</p>\n\n'
           f'{parts["Now"]}\n\n</div>')
    return (markdown
            .replace("<!-- progress:updated -->", updated)
            .replace("<!-- progress:now -->", now)
            .replace("<!-- progress:milestones -->",
                     _timeline(parts["Milestones"]))
            .replace("<!-- progress:latest -->",
                     "\n\n".join(entries[:LATEST])))


@functools.lru_cache(maxsize=None)
def _published() -> frozenset[str]:
    """Every path GitHub has: tracked files and their directories. A
    gitignored file (application/, data/external/) exists on this disk but
    not on GitHub, so existence alone is the wrong test."""
    listing = subprocess.run(["git", "ls-files"], cwd=ROOT, check=True,
                             capture_output=True, text=True).stdout
    paths = set()
    for f in listing.splitlines():
        while f:
            paths.add(f)
            f = posixpath.dirname(f)
    return frozenset(paths)


def _relink(markdown: str, page, files) -> str:
    here = posixpath.dirname(SOURCE.get(page.file.src_uri,
                                        page.file.src_uri))

    def fix(match):
        text, target = match.group(1), match.group(2)
        if re.match(r"^[a-z]+:|^#|^/", target):
            return match.group(0)
        path, _, anchor = target.partition("#")
        resolved = posixpath.normpath(posixpath.join(here, path))
        if files.get_file_from_path(resolved) is not None:
            return match.group(0)
        if resolved not in _published():
            return match.group(0)        # let MkDocs report it
        kind = "tree" if (ROOT / resolved).is_dir() else "blob"
        url = f"{REPO}/{kind}/main/{resolved}"
        return f"[{text}]({url}{'#' + anchor if anchor else ''})"

    return _LINK.sub(fix, markdown)


def on_page_markdown(markdown, page, config, files, **kwargs):
    if page.file.src_uri == "index.md":
        markdown = _home(markdown)
    return _relink(markdown, page, files)
