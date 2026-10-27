# STAR on Atoms — Outline, Commitments & Schedule

> **Status of this document:** living blueprint and *the contract*. Chapters
> may split, merge or reorder as drafts reveal what the work needs — but
> every change lands here first, so this file is always the current plan.
>
> **Started:** Mon 2026-10-26 · **Results freeze:** Wed 2026-11-04 ·
> **Application target:** Fri 2026-11-06 (hard deadline Tue 2026-11-10;
> QuEra guarantees full consideration before Sun 2026-11-15).
>
> **Primary stack:** QuEra's published STAR circuits (fetched, pinned,
> hash-checked) · **tsim** for every non-Clifford sample · **stim +
> PyMatching** for detector error models and decoding · **bloqade-circuit**
> for the Gemini heuristic noise models. Shipped artifact: **`starlab`**.

---

## The question

Transversal STAR (space-time efficient analog rotation) is QuEra's
proposal for running the megaquop regime: inject small-angle rotations by
post-selection instead of distilling T gates. Its usefulness is capped by
one number — the coefficient α in the teleported rotation error
p_L(θ) ≈ α·p·θ — through the rotation budget Σ|θ| ≲ 1/(α p) and a
simulation volume that scales as 1/(α p)² [Ismail et al. 2026, PRX Quantum
7, 020343; arXiv:2606.25011].

Both papers fold the physical noise into a single knob p. Neither, in the
text read on 2026-10-26, varies the physical channels one at a time. A
hardware team has to choose *which* error to halve next.

> **Which physical noise channel limits transversal STAR on neutral atoms,
> and how much simulation volume would halving each one buy?**

Answering it means (1) reproducing QuEra's published uniform-noise STAR
curve with this book's own pipeline, (2) re-noising the same circuits with
channel-resolved, hardware-aware models, (3) scanning each channel while
holding the rest fixed, and (4) propagating the measured changes in α and
in acceptance through the published budget formulas.

## The book's two jobs

1. **Run one experiment honestly** — pre-registered, reproducible, every
   number with its interval.
2. **Leave its author able to defend every line without notes.** The
   hiring bar this book is written against is a whiteboard: derive the
   STAR acceptance, explain why reaction time sets the clock, say which
   assumption moves the headline most. So mastery is a recurring,
   machine-checked element of every chapter, not an afterthought.

## Commitments (each enforced by a guard)

| # | Commitment | Enforced by |
|---|---|---|
| 1 | Every protocol is committed before any result it describes exists | `tools/check_protocols.py` (git commit date vs. artifact `captured`) |
| 2 | Every measured rate carries its shots, errors, seed, environment and 95% interval | `tools/check_results.py` |
| 3 | No claim is cited from memory: every DOI and arXiv ID resolves to the title written | `tools/check_citations.py` (`make release`) |
| 4 | Every chapter keeps the contract below | `tools/check_structure.py` |
| 5 | Every chapter discloses what an AI agent did, what was verified by hand, and what the agent got wrong | the 🤖 Agent Log, required by `check_structure.py` |
| 6 | Inputs we do not own are never redistributed: QuEra's circuits are fetched at a pinned commit and hash-checked | `tools/fetch_star_circuits.py` |

## The chapter contract

| Element | Rule | Why |
|---|---|---|
| 🎯 Learning Goals | exactly one, opening | the chapter's promise |
| 🧑‍🏫 Whiteboard | ≥ 1 | a derivation to reproduce at a board with no notes and no agent |
| 🔬 Evidence | ≥ 1 in Part III | a measured number with its provenance |
| 🤖 Agent Log | exactly one | delegated / verified by hand / agent errors caught |
| 🎤 Interview Drill | ≥ 1 box, ≥ 3 questions | what a QuEra interviewer would ask about this chapter |
| 💪 Exercises | ≥ 4 numbered | practice that builds the whiteboard skill |
| 🔤 Vocabulary | optional | the word in a paper, and what it is |

---

## Plan of the book

Status key: ✅ drafted · 🟡 in progress · ⬜ planned

### Part I — The Question
| Ch | Title | Status | Protocol |
|---|---|---|---|
| 1 | The question, the bet, and the plan | ✅ | — |

### Part II — Crash Course (for a reader starting from very little)
Each chapter: ~90 minutes, executable checks of every claim, a ⏱️
60-Second Answer, and a drill with model answers. Added 2026-10-26 at the
author's request, from the interview topics the reviewers named.

| Ch | Title | Status |
|---|---|---|
| 2 | Codes you must be able to draw: surface, color, and transversal gates | ✅ |
| 3 | Magic: distillation and cultivation | ✅ |
| 4 | Neutral atoms as a machine: Rydberg blockade and atom shuttling | ✅ |
| 5 | Simulating a lattice: Trotter error and the Jordan–Wigner mapping | ✅ |

### Part III — The STAR Machinery
| Ch | Title | Status | Protocol |
|---|---|---|---|
| 6 | One small rotation: STAR injection from first principles | ✅ | — |
| 7 | Memory and matching: detectors, error models, and the Clifford proxy | ✅ | — |
| 8 | The noise menu: every way an atom array fails, as a Pauli channel | ⬜ | — |
| 9 | From an injected state to a teleported rotation: α and the budget | ⬜ | — |

### Part IV — The Experiment
| Ch | Title | Status | Protocol |
|---|---|---|---|
| 10 | Reproducing QuEra's curve | ✅ | P01 (REPORTED 2026-10-27: refuted as registered; see LEDGER) |
| 11 | Re-noising: from uniform to hardware-aware | ⬜ | P02 |
| 12 | The per-channel scan | ⬜ | P03 |
| 13 | What a factor of two buys | ⬜ | P03 (analysis) |
| 14 | Threats to validity | ⬜ | — |

### Part V — After the application
| Ch | Title | Status | Protocol |
|---|---|---|---|
| 15 | d = 7 and beyond: sampling on a GPU | ⬜ | P04 |
| 16 | Atom loss as erasure | ⬜ | P05 |
| 17 | Upstream: what this project gave back | ⬜ | — |

### Appendices
| App | Title | Status |
|---|---|---|
| A | Reproducing this book | ✅ |
| B | The interview drill bank (every 🎤 box, with model answers) | ⬜ |
| C | The agent log index (every 🤖 box, collected) | ⬜ |

---

## Schedule (15 days)

Two tracks run every day: **study** (morning, ~90 min, Part II then the
STAR chapters) and **project** (the rest). Study comes first because the
project chapters assume it.

| Date | Study track | Project track | Done when |
|---|---|---|---|
| **Mon 10-26** | — | Repo, guards, PDF; P01 registered and run; Ch 1–3, 6–7 drafted; crash course drafted | `make check` green |
| Tue 10-27 | **Ch 2** codes & transversal gates | P01 diagnostics R3/R4; Ch 10 written; P01 settled | P01 verdict in LEDGER.md |
| Wed 10-28 | **Ch 3** magic states | Ch 8 (noise menu, pinned from the PDF); **P02 registered** (re-noiser) | P02 committed |
| Thu 10-29 | **Ch 4** Rydberg atoms | P02 run: uniform vs. hardware-aware vs. bloqade Gemini; Ch 11 | re-noiser reproduces P01 at uniform settings |
| Fri 10-30 | **Ch 5** Trotter & Jordan–Wigner | **P03 registered**; scan launched | P03 committed before first sample |
| Sat 10-31 | Ch 2–5 whiteboards **cold** (no notes) | scan runs; Ch 9 | — |
| Sun 11-01 | **Ch 6–7** + their whiteboards cold | Ch 12 (per-channel tornado) | — |
| Mon 11-02 | Mock interview #1 (agent as interviewer, Part II drills) | Ch 13: headline figure and answer | one-paragraph answer |
| Tue 11-03 | Ch 2–5 whiteboards cold, second day | Ch 14 threats; one upstream issue/PR | — |
| **Wed 11-04** | — | **FREEZE.** README, repo public, 2–3 page note | `make release` green |
| Thu 11-05 | Mock interview #2 (whole book) | Resume, site, cover letter (`application/`); re-run reviewer agents | verdicts recorded |
| **Fri 11-06** | — | **Submit** | confirmation email |
| Sat 11-07 – Tue 11-10 | Drill bank, weakest chapter first | buffer only | — |

**Scope guard.** If P02 is not producing trustworthy numbers by the end of
Thu 10-29, P03 shrinks to d = 3 only and the cut is recorded here. The study
track is not cut: it is what the interview tests.

## Mastery plan

- **Every Whiteboard box is practised cold**: no notes, no agent, timed,
  on paper. A box counts as mastered when it has been reproduced correctly
  on two different days. Appendix B tracks this.
- **Every ⏱️ 60-Second Answer is said out loud**, timed, until it fits in
  a minute without reading. These are the answers to the four topics the
  reviewers said an interview will probe.
- **Mock interviews** on Thu 11-05 and again after submission, using the
  🎤 drill bank, with an agent playing the interviewer and grading against
  the model answers.
- **The 🤖 Agent Log is the honesty ledger for the hiring conversation**:
  for every chapter, the author can say exactly what was delegated and
  what was checked by hand.

## Open questions (resolve before they bite)

1. What exactly is "logical error rate / distance" in QuEra's plot? P01
   pre-registers three alternative normalisations in case the primary one
   is off by a common factor.
2. Where do atom moves belong in a CX-based circuit? The published circuits
   have no move instructions; P02 must state a placement rule and sweep it.
3. α is defined for the *teleported* rotation; the published circuits
   measure the *injected* state. Ch 5 must derive the relation used, or
   P03 must report injection infidelity under its own name.
