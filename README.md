# STAR on Atoms

**Which physical noise channel limits transversal STAR on neutral atoms —
and how much simulation volume would halving each one buy?**

A research log and a mastery course in one. This repository is a
[Quarto](https://quarto.org) book whose every chapter is executable, plus
the small library (`starlab`) and the pre-registered protocols behind it.
It studies QuEra's *transversal STAR* architecture — post-selected
small-angle rotation injection for the early-fault-tolerant "megaquop"
regime — using QuEra's own published circuits and open-source tools
(tsim, bloqade, stim).

> **Status (2026-10-27):** 🚧 Chapters 1–10 drafted, including a
> four-chapter crash course (codes, magic states, Rydberg atoms, Trotter and
> Jordan–Wigner). Protocol P01 is settled. QuEra's published curve is
> reproduced only under a decoder that drops faults flipping more than two
> detectors (P01-R6), and its large-angle regime is a read-out artifact
> (P01-R7). Protocol P02 (QuEra's Table II hardware noise, rebuilt on native
> gates and validated) is running.
>
> **Where things stand, by date:** the
> [project site](https://mamuncseru.github.io/star-on-atoms/) and
> [PROGRESS.md](PROGRESS.md). [OUTLINE.md](OUTLINE.md) is the plan and the
> schedule; [LEDGER.md](LEDGER.md) records every verdict.

## Why this exists

The useful reach of transversal STAR is capped by one coefficient: a
teleported rotation by θ fails with probability ≈ α·p·θ, so a computation
can afford a total rotation of only about 1/(α p): its simulation volume
(sites × simulated time) scales as 1/(α p), and its circuit volume (sites ×
Trotter steps) as 1/(α p)². QuEra's papers scale every physical noise
channel together by one knob, p. A hardware programme has to decide which
error to halve next. This book measures that — an error budget for STAR
injection under QuEra's published hardware model, one channel at a time,
with intervals — on a pipeline first shown to reproduce QuEra's published
curve.

## What makes it trustworthy

- **Pre-registration, enforced.** Every experiment is a protocol in
  [`protocols/`](protocols/), committed before it runs; a guard compares
  git commit dates with the dates inside every result file.
- **Every rate is a measurement** with shots, logical errors, seed,
  environment and a 95% Wilson interval, checked by a guard.
- **Validation before novelty.** Nothing new is claimed until the
  pipeline reproduces QuEra's own uniform-noise STAR curve (Protocol P01).
- **Inputs are pinned, not copied.** QuEra's circuits are fetched at one
  commit and checked by SHA-256; the upstream repository has no license, so
  they are never redistributed here.
- **AI use is disclosed per chapter.** Every chapter carries a 🤖 Agent
  Log: what an agent did, what was verified by hand, and what the agent
  got wrong.

## Building locally

```bash
# 1. Environment (Python 3.11). On hosts with glibc < 2.35 there is no
#    pyqrack wheel; this book never uses PyQrack, so install bloqade-circuit
#    without dependencies after the rest.
python -m venv ~/.venvs/star-book && source ~/.venvs/star-book/bin/activate
pip install -r requirements.txt
pip install --no-deps bloqade-circuit==0.15.3
pip install -e .

# 2. Register the kernel Quarto is pinned to, and capture the environment
python tools/install_kernel.py

# 3. Fetch QuEra's circuits (pinned + hash-checked), then verify everything
make fetch
make check

# 4. Render website + PDF into book/_book/
make book
```

## Repository layout

```
book/          Quarto source — one source for website and PDF
  chapters/    One .qmd per chapter, by part
  appendices/  Back matter
  styles/      Design system: palette, figure style, web themes, PDF template
  bib/         references.bib — every ID resolved before release
starlab/       The library: circuits at any angle, sampling, statistics
tests/         Tests for starlab, against facts that exist independently of it
tools/         Guards, the circuit fetcher, the digitizer, protocol runners
protocols/     Pre-registered experiments (committed before they run)
data/
  reference/   QuEra's reference plot, digitized from its SVG
  results/     Dated, committed measurements
  external/    Fetched inputs (git-ignored)
OUTLINE.md     The contract and the schedule
LEDGER.md      Every verdict, with what would change it
```

## The guards

`make check` runs, cheapest first:

| Guard | What it prevents |
|---|---|
| `tools/check_math.py` | LaTeX that renders on the web and silently corrupts the PDF |
| `tools/check_structure.py` | A chapter dropping a mastery element (🎯 🧑‍🏫 🤖 🎤 💪, 🔬 in Part III) |
| `tools/check_citekeys.py` | A citation whose key is not in the bibliography |
| `tools/check_results.py` | A committed rate without its shots, seed, environment or interval |
| `tools/check_protocols.py` | A result that predates its own protocol |
| `tests/test_starlab.py` | The library being wrong |
| `tools/check_code.py` | Over-long listings, palette drift, broken companion scripts |

`make release` adds `tools/check_citations.py`, which resolves every DOI
and arXiv ID and compares the returned title with the one cited.

## Credits

The STAR circuits and the reference plot are QuEra Computing's, published
for the ETH QHack 2026 challenge
([QuEraComputing/ETH_QHACK_2026](https://github.com/QuEraComputing/ETH_QHACK_2026)).
The transversal STAR architecture is from Ismail *et al.*, PRX Quantum 7,
020343 (2026), building on Akahoshi *et al.*, PRX Quantum 5, 010337 (2024).
The book's design system and guards are shared with the author's sister
volumes.

## License

- **Text and figures:** [CC BY 4.0](LICENSE-TEXT.md)
- **Code, including `starlab`:** [MIT](LICENSE)
