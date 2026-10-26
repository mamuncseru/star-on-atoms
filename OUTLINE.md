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

### Part II — Foundations (the mastery half)
| Ch | Title | Status | Protocol |
|---|---|---|---|
| 2 | One small rotation: STAR injection from first principles | ✅ | — |
| 3 | Memory and matching: detectors, error models, and the Clifford proxy | ⬜ | — |
| 4 | Neutral atoms as a machine: zones, moves, CZ, loss — and the noise menu | ⬜ | — |
| 5 | From one rotation to a simulation: Trotter steps, the rotation budget, simulation volume | ⬜ | — |

### Part III — The Experiment
| Ch | Title | Status | Protocol |
|---|---|---|---|
| 6 | Reproducing QuEra's curve | 🟡 | P01 (registered 2026-10-26) |
| 7 | Re-noising: from uniform to hardware-aware | ⬜ | P02 |
| 8 | The per-channel scan | ⬜ | P03 |
| 9 | What a factor of two buys | ⬜ | P03 (analysis) |
| 10 | Threats to validity | ⬜ | — |

### Part IV — After the application
| Ch | Title | Status | Protocol |
|---|---|---|---|
| 11 | d = 7 and beyond: sampling on a GPU | ⬜ | P04 |
| 12 | Atom loss as erasure | ⬜ | P05 |
| 13 | Upstream: what this project gave back | ⬜ | — |

### Appendices
| App | Title | Status |
|---|---|---|
| A | Reproducing this book | ✅ |
| B | The interview drill bank (every 🎤 box, with model answers) | ⬜ |
| C | The agent log index (every 🤖 box, collected) | ⬜ |

---

## Schedule (15 days)

| Date | Work | Done when |
|---|---|---|
| **Mon 10-26** | Repo, environment, guards, PDF; P01 registered and run; Ch 1–2 drafted | `make check` green, PDF renders, P01 artifacts committed |
| Tue 10-27 | Ch 6 from P01 (pass/fail analysis); Ch 3 drafted; read PRX Quantum App. D & G in full | P01 verdict in LEDGER.md |
| Wed 10-28 | Ch 4 (atoms + noise menu); **P02 registered**: re-noiser design (CX → H·CZ·H, channel classes, move/loss placement) | P02 committed; re-noiser reproduces P01 exactly at uniform settings |
| Thu 10-29 | P02 run: uniform vs. Table-2 hardware-aware vs. bloqade Gemini model | Ch 7 drafted |
| Fri 10-30 | **P03 registered**: scan grid, metric, budget; scan launched | P03 committed before first scan sample |
| Sat 10-31 – Sun 11-01 | Scan completes; Ch 8; Ch 5 | per-channel tornado figure |
| Mon 11-02 | Ch 9: propagate to simulation volume; headline figure | one-paragraph answer to the question |
| Tue 11-03 | Ch 10 threats to validity; one upstream issue or PR from real friction | issue/PR link in Ch 13 stub |
| **Wed 11-04** | **FREEZE.** README headline; repo public; 2–3 page technical note | `make release` green |
| Thu 11-05 | Resume, site, cover letter (in `application/`, local only); re-run both reviewer agents on the real artifact; mock interview from the drill bank | reviewer verdicts recorded |
| **Fri 11-06** | Fixes; **submit** | confirmation email |
| Sat 11-07 – Tue 11-10 | Buffer only. Nothing new starts. | — |
| After | Part IV; interview preparation from Appendix B | — |

**Scope guard.** If P02 is not producing trustworthy numbers by the end of
Thu 10-29, P03 shrinks to d = 3 only and the cut is recorded here.

## Mastery plan

- **Every Whiteboard box is practised cold**: no notes, no agent, timed,
  on paper. A box counts as mastered when it has been reproduced correctly
  on two different days. Appendix B tracks this.
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
