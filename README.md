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

## The answer so far

Under QuEra's Table II hardware model at p_ph = 10⁻³, for QuEra's
published STAR circuits at d = 3, 5 and 7:

- **Single-qubit gates carry the largest share of the injection error,
  43–52%, but the rotation gate itself carries only 12–16%.** The rest is
  the Hadamards that the CNOT-to-CZ compilation leaves on data qubits.
  Spectators and the CZ carry about a quarter each. Initialization,
  measurement and atom loss (a Y error, as Table II models it) carry
  nothing at first order: they cost acceptance only.
- **Halving single-qubit-gate error buys ×1.32 in simulation volume at
  d = 5** (sampled: ×1.36, 95% interval 1.21–1.52).
- **In syndrome extraction, the CZ's correlated ZZ error, its largest
  term, costs this injection nothing**, because every ancilla is prepared
  and measured in X. This holds for a single-qubit rotation gate. In STAR
  protocols that rotate with two-qubit R_ZZ gates, a ZZ at the rotation is
  the critical fault (Veroni, Deger and Daley, arXiv:2610.26471).
- **How it was measured.** An exact first-order count over every fault
  in the circuits' own error model ([`starlab/enumerate.py`](starlab/enumerate.py))
  was committed as a prediction, then tested blind on 802 million sampled
  shots, including d = 7 ([P04](protocols/P04-sampled-budget-blind-test.md),
  CONFIRMED).

The three-page summary is the [note (PDF)](docs/downloads/star-on-atoms-note.pdf)
([source](note/star-on-atoms-note.qmd); `make note` renders it). Every verdict, with what would overturn
it, is in [LEDGER.md](LEDGER.md).

> **Status (2026-10-30):** results frozen at tag
> [`results-freeze-2026-10-30`](https://github.com/mamuncseru/star-on-atoms/tree/results-freeze-2026-10-30): every protocol is reported and every verdict is in
> the ledger. The book's sources (Chapters 1–13) are in this repository.
> Its rendered edition will be published after the application, once the
> author has verified each chapter's Agent Log by hand. Dated progress is on the
> [project site](https://mamuncseru.github.io/star-on-atoms/) and in
> [PROGRESS.md](PROGRESS.md); [OUTLINE.md](OUTLINE.md) is the plan.

## Why this exists

The useful reach of transversal STAR is capped by one coefficient: a
teleported rotation by θ fails with probability ≈ α·p·θ, so a computation
can afford a total rotation of only about 1/(α p): its simulation volume
(sites × simulated time) scales as 1/(α p), and its circuit volume (sites ×
Trotter steps) as 1/(α p)². QuEra's papers scale every physical noise
channel together by one knob, p. A hardware programme has to decide which
error to halve next. This book measures that — an error budget for STAR
injection under QuEra's published hardware model, one channel at a time,
with intervals — on a pipeline first shown to reproduce the reference
curve in QuEra's challenge repository.

## What makes it trustworthy

- **Pre-registration, enforced.** Every experiment is a protocol in
  [`protocols/`](protocols/), committed before it runs; a guard compares
  git commit dates with the dates inside every result file.
- **Every rate is a measurement** with shots, logical errors, seed,
  environment and a 95% Wilson interval, checked by a guard.
- **Validation before novelty.** The rebuilt circuits reproduce QuEra's
  published error model exactly before any new noise model is used
  (P02), and the calculator was tested blind before its budget was
  reported (P04).
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
note/          The three-page summary for readers who will not open the book
starlab/       The library: circuits at any angle, re-noising, sampling,
               the exact first-order count, statistics
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
| `tools/check_structure.py` | A chapter dropping a mastery element (🎯 🧑‍🏫 🤖 🎤 💪, 🔬 in Part IV) |
| `tools/check_citekeys.py` | A citation whose key is not in the bibliography |
| `tools/check_results.py` | A committed rate without its shots, seed, environment or interval |
| `tools/check_protocols.py` | A result that predates its own protocol |
| `tests/test_starlab.py` | The library being wrong |
| `tools/check_code.py` | Over-long listings, palette drift, broken companion scripts |

`make release` adds `tools/check_citations.py`, which resolves every DOI
and arXiv ID and compares the returned title with the one cited.

## Credits

**Upstream.** A decoding pitfall found along the way (matching on tsim's
default error model silently drops faults that flip more than two
detectors) is reported as [tsim issue #232](https://github.com/QuEraComputing/tsim/issues/232).
At a maintainer's request, [pull request #234](https://github.com/QuEraComputing/tsim/pull/234) adds the warning to
the docstring and lets `detector_error_model(decompose_errors=True)` pass
through to stim.

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
