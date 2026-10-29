---
title: Home
hide:
  - navigation
---

# STAR on Atoms

Small-angle rotations under real neutral-atom noise: a research log and a
mastery course, written in the open.

Transversal STAR prepares small-angle rotations by post-selection, cheaply
enough that an early fault-tolerant machine might run useful simulations
with them. Its reach is capped by one coefficient: a teleported rotation by
θ fails with probability ≈ α·p·θ, so a computation can afford a total angle
of only about 1/(α·p). QuEra's papers move every noise channel together
through one knob, *p*. This project asks which physical channel actually
sets α on a neutral-atom machine, and what halving each one would buy. It
measures this on QuEra's own published circuits, under QuEra's own
published hardware noise model, with every experiment registered before it
runs.

<p class="soa-meta" markdown="span">Started 2026-10-26 · results freeze
2026-10-30 · last update <!-- progress:updated --> ·
[source on GitHub](https://github.com/mamuncseru/star-on-atoms) ·
text CC BY 4.0, code MIT</p>

## Where we are

<!-- progress:now -->

## Timeline

<!-- progress:milestones -->

## Latest progress

<!-- progress:latest -->

[The full progress log →](PROGRESS.md)

## What we have found so far

Every claim has a row in the [ledger](LEDGER.md), with its verdict and the
result that would overturn it.

- **The reference STAR curve in QuEra's challenge repository depends on its
  decoder.** It is reproduced
  only when the samples are decoded by matching on tsim's default error
  model. PyMatching silently drops that model's faults that flip more than
  two detectors, 19% of the fault probability at d = 3. Decoded correctly,
  the d = 3 floor is about 9× lower
  ([P01-R6](protocols/P01-reproduce-uniform-star.md)).
- **The published circuits' large-angle error is mostly not injection.** It
  is memory-round errors read out through the perfect unrotation, ∝ sin²θ.
  That is why the larger code looks worse at large angles
  ([P01-R7](protocols/P01-reproduce-uniform-star.md)).
- **The paper's noise table, read exactly.** Its Eq. D1 sums to
  7.46 × 10⁻³, not the quoted 7.3 × 10⁻³. And its prose and its table
  disagree about the single-qubit gate channel. Both are recorded in
  [P02](protocols/P02-renoise-table-ii.md).
- **The injection error, computed exactly.** Matching every possible fault
  against the rotation's branches reproduces 665 million sampled shots
  with no fitted parameter ([P03](protocols/P03-exact-first-order.md)).
  Only single *Z* faults on the rotated qubits survive post-selection.
  Initialization, measurement and atom loss (a *Y* error, as the paper's
  table models it) cost shots, and no fidelity at first order.
- **The budget, tested blind.** The calculation's predictions, committed
  before sampling, match every noise channel alone and d = 7, which had
  never been sampled ([P04](protocols/P04-sampled-budget-blind-test.md)).
  Single-qubit gates carry the largest share (43–52% at d = 3–7), but the
  rotation gate itself only 12–16%. Halving single-qubit-gate error buys
  ×1.32 in simulation volume at d = 5 (sampled: ×1.36).
  In syndrome extraction, the CZ's correlated *ZZ* error, its largest
  term, costs this injection nothing. That is specific to a single-qubit
  rotation gate.
- **α is decided at large angles.** Composed through the paper's
  repeat-until-success sum (its Eq. 4), the injections at π/4 to π/16 carry
  61–79% of α. A budget measured there sets α.

## How the work is done

1. **Pre-registration, enforced.** Every experiment is a
   [protocol](protocols/P02-renoise-table-ii.md) committed before it runs,
   and a guard fails the build if a result predates its protocol.
2. **Every rate is a measurement.** Each comes with its shots, errors,
   seed, environment and a 95% Wilson interval, also checked by a guard.
3. **Failures are published.** P01 failed as registered; it stays in the
   ledger as REFUTED, next to the diagnosis that explained it.
4. **Credit is checked against the PDF.** When the paper already had a
   result the project rediscovered, the protocol says so, dated before
   the results were read.
5. **The agent's work is accounted for.** The project is written with an AI
   agent (Claude). Every chapter of the book ends with an Agent Log: what
   was delegated, what the author verified by hand, and what was caught.
   The book is released only when every box is ticked.

## Where to start

| If you want to… | Read |
|---|---|
| know where the project stands today | [Progress](PROGRESS.md) |
| check a claim | [The ledger](LEDGER.md) |
| see an experiment's rules before its results | [P01](protocols/P01-reproduce-uniform-star.md), [P02](protocols/P02-renoise-table-ii.md) |
| see the plan, the chapters and the schedule | [The plan](OUTLINE.md) |
| reproduce a number | [About the repository](about.md) |
