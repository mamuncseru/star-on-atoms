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
p_L(θ) ≈ α·p·θ — through the rotation budget Σ|θ| ≲ 1/(α p): simulation
volume N_sT ∝ 1/(αp) (Eq. 5) and circuit volume N_sN_tr ∝ 1/(αp)² (Eq. 8)
[Ismail et al. 2026, PRX Quantum 7, 020343; arXiv:2606.25011].

Both papers scale every physical channel together by one knob p (the
second uses uniform noise only). The PRX paper's App. D.2 argues per-channel
improvement targets qualitatively and App. G.3 compares whole noise
models; neither measures each channel's share of STAR's injection error
(checked in the PDF, 2026-10-27). A hardware team has to choose *which*
error to halve next.

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
| 8 | The noise menu: Table II of the PRX paper as Pauli channels (a short chapter: one table, pinned from the PDF) | ✅ | — |
| 9 | From an injected state to a teleported rotation: α via Eq. 4 (a short whiteboard chapter) | ✅ | — |

### Part IV — The Experiment
| Ch | Title | Status | Protocol |
|---|---|---|---|
| 10 | Reproducing QuEra's curve | ✅ | P01 (REPORTED 2026-10-27: refuted as registered; see LEDGER) |
| 11 | Re-noising: Table II in stim, validated | ✅ | P02 (REPORTED 2026-10-27: H2 confirmed) |
| 12 | An error budget for STAR injection (shares, additivity, what halving buys) | ⬜ | P03 |
| 13 | Threats to validity | ⬜ | — |

### Part V — After the application (deferred 2026-10-27; nothing here starts before 11-06)
| Ch | Title | Status | Protocol |
|---|---|---|---|
| 14 | The paper's own protocol: k = 3 TMR, then a high-rate STAR gadget | ⬜ | P04 |
| 15 | Upstream: what this project gave back | ⬜ | — |

Cut 2026-10-27 on advisor recommendations (see `application/advisors/DECISIONS.md`,
local): the bloqade Gemini simulation mode, the ×2 arms, d = 7, and the
atom-loss-as-erasure chapter (arXiv:2606.25011 already reports the
heralded-loss scaling).

### Appendices
| App | Title | Status |
|---|---|---|
| A | Reproducing this book | ✅ |
| B | The interview drill bank — after submission | ⬜ |
| C | The agent log index — after submission | ⬜ |

**Freeze rule (2026-10-27).** At the freeze, any chapter whose 🤖 Agent Log
still has unticked "Verified by hand" boxes is removed from the public
build's `_quarto.yml` until the author has checked it.

---

## Schedule (15 days)

Two tracks run every day: **study** (morning, ~90 min, Part II then the
STAR chapters) and **project** (the rest). Study comes first because the
project chapters assume it.

| Date | Study track | Project track | Done when |
|---|---|---|---|
| **Mon 10-26** | — | Repo, guards, PDF; P01 registered and run; Ch 1–3, 6–7 drafted; crash course drafted | `make check` green |
| Tue 10-27 | **Ch 2** codes & transversal gates | P01 diagnostics R3–R7 (cause found: R6 decoder, R7 read-out artifact); Ch 10; advisors consulted; volume exponent fixed | ✅ P01 settled in LEDGER.md |
| Tue 10-27 (evening, pulled forward) | — | Repo pushed (public); QAQ fix pushed; tsim issue finalised for the author; Ch 8; `starlab/renoise.py` validated (V1 exact at d = 3, 5, 7); **P02 registered and run** | ✅ P02 committed before its first sample |
| Wed 10-28 | **Ch 7** memory, matching & DEMs + Ch 10's three whiteboards (the project's own story) | P02 analysis → Ch 11; **P03 registered** (error budget, design set by P02's H2) and launched | P03 committed before first sample |
| Thu 10-29 | **Ch 3** magic states (skim derivations; 60-second answer cold) + Ch 11's misrotation whiteboard | P03 analysis; Ch 12 draft | — |
| Fri 10-30 | **Read** PRX paper Sec. II–III (esp. Eq. 2), App. D, G in the PDF | Ch 9 (α via Eq. 4, and how it relates to Eq. 2's misrotation term); Ch 12 headline figure | — |
| Sat 10-31 | **Ch 5** Trotter & JW; Ch 6 STAR whiteboard cold | P03 analysis; Ch 9 (α via Eq. 4); Ch 12 | — |
| Sun 11-01 | **Ch 4** Rydberg (60-second answer; skim pulse derivations); fix site, resume header, pinned repos | Ch 12 headline figure | — |
| Mon 11-02 | Mock interview #1 (agent as interviewer) | 2–3 page note; Ch 13 threats | one-paragraph answer |
| Tue 11-03 | Six core whiteboards cold, second day | README headline; tick-or-remove pass on every Agent Log | — |
| **Wed 11-04** | — | **FREEZE.** repo public; `make release` | `make release` green |
| Thu 11-05 | Mock interview #2 — with a human if possible | Cover letter (`application/`); re-run the two hiring reviewers on the real artifact | verdicts recorded |
| **Fri 11-06** | — | **Submit** | confirmation email |
| Sat 11-07 – Tue 11-10 | Drill bank, weakest chapter first | buffer only | — |

**Scope guard.** If the re-noiser is not validated by the end of Fri 10-30,
ship what is solid (P01 and its eight diagnostics, the note, the upstream
finding) and register P03 as post-submission work. The study track is not
cut: it is what the interview tests.

**Six core whiteboards** (the ones to master first, on two different days):
transversal CNOT (Ch 2), STAR acceptance and angle (Ch 6), the Clifford
proxy (Ch 7), why dropped hyperedges raise the floor (Ch 10), the sin²θ
read-out artifact (Ch 10), and simulation vs. circuit volume (Ch 1).

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
