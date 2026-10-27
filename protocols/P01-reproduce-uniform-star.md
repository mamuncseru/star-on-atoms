# Protocol P01: reproduce QuEra's uniform-noise STAR curve

- **Status:** RUN
- **Chapter:** 10
- **Registered:** 2026-10-26
- **Artifacts:** p01_uniform_star_d3, p01_uniform_star_d5

## The question

Does this book's pipeline — QuEra's published STAR circuits, re-angled by
`starlab.with_angle`, sampled with tsim, post-selected on the injection
rounds and decoded by minimum-weight matching — reproduce the logical error
rates in QuEra's published reference plot for d = 3 and d = 5?

Every later number in this book is a change relative to this pipeline. If it
cannot reproduce the published curve under the published noise, nothing
built on it is evidence, so this protocol is a gate: Protocols P02 and P03
may not run until P01 passes or its failure is explained.

## Circuits and noise

- Circuits: `star_d=3.stim` and `star_d=5.stim` from
  QuEraComputing/ETH_QHACK_2026 at commit `393312b5de`, SHA-256 checked by
  `tools/fetch_star_circuits.py`. Unmodified except for the two `R_Z` lines
  that set the angle.
- Noise: exactly as published — `DEPOLARIZE1(0.001)` and
  `DEPOLARIZE2(0.001)` as written in the files, noise disabled after
  `TICK[DISABLE_ERROR]`. Nothing added, nothing removed.
- Angles (logical, radians): θ_i = 10^(−4 + 0.6 i), i = 0 … 7. This is the
  grid recovered from the reference SVG by `tools/digitize_reference.py`
  (`data/reference/eth_qhack_2026_star_sim.json`), committed with this
  protocol.
- d = 7 is out of scope here: at the published floor (~1e-5 absolute) it
  needs ~10^7 accepted shots per point. It is deferred to a later protocol
  with GPU sampling.

## Method

`starlab.sampling.sample_star`, as committed with this protocol:

1. tsim `compile_detector_sampler(seed=…)`, default strategy, compiled
   once per point and drawn from in batches of 100,000 shots.
2. Accept a shot iff its first 3(d² − 1) detectors are all zero.
3. Decode each accepted shot's full detector record with PyMatching 2.4 on
   the detector error model of the circuit's **Clifford proxy**:
   `circuit.stim_circuit`, in which stim reads every tsim rotation as a
   tagged identity, so the circuit is the same one at θ = 0
   (`detector_error_model(decompose_errors=True)`, decomposition failures
   not ignored). tsim itself refuses to decompose a model whose observable
   is non-deterministic. The proxy is exact for every Pauli error after the
   injection layer, which is all the decoder is asked to correct; errors
   before or during injection are post-selection's responsibility.
4. A logical error is a decoded observable that differs from the measured
   one. Rate = logical errors / accepted shots.
5. Reported quantity, to match the plot's y-axis: rate / d.

## Budget

- Shots sampled per point: 1,000,000 at d = 3; 4,000,000 at d = 5.
  At the published floors and the observed d = 3 acceptance (~0.68 in a
  smoke test), that is ~4,000 errors per d = 3 point (±3%) and, at an
  assumed acceptance ≥ 0.3, ≥ 150 errors per d = 5 point (±16%).
- Seeds: point i at distance d uses `seed = 20261026 + 1000·d + i`; one
  seeded sampler per point, batches of 100,000 drawn in sequence.
- Ceiling: 2 CPU-hours for the whole protocol on the author's workstation.
  A point not finished inside the ceiling is reported as not run.

## Metrics and acceptance criteria

Let r_i = (this book's rate/d) ÷ (digitized reference value), over the 16
points (2 distances × 8 angles).

- **Primary:** the geometric mean of r_i lies in [0.80, 1.25], **and** no
  single r_i lies outside [0.5, 2.0].
- **Reported, not pass/fail:** how many of the 16 reference values fall
  inside this book's 95% Wilson interval. The reference values carry their
  own unknown sampling noise (the d = 5 floor visibly jitters by ~35%
  between neighbouring angles), so a per-point containment test would fail
  for reasons that are not ours.
- **Reported:** acceptance at every point, against the noiseless ideal
  cos^{2k}(θ*/2) + sin^{2k}(θ*/2).

## Stopping rule

Every point is run once, at the budget above, with the seeds above. No
re-runs with fresh seeds. A crash is re-run with the same seed and recorded
under Deviations.

## What each outcome means

- **Pass:** the pipeline reproduces QuEra's published numbers under QuEra's
  noise, and becomes the baseline for P02 and P03. It establishes nothing
  about hardware-aware noise; that is P02's question.
- **Fail by a common factor** (all r_i within ±20% of one constant c that
  is outside [0.8, 1.25]): the plot normalises differently. Exactly these
  three alternatives are checked, in this order, and the first that passes
  is adopted and recorded as a deviation: (a) rate undivided by d;
  (b) rate divided by the d + 3 noisy rounds; (c) rate per sampled shot
  rather than per accepted shot. If none passes, P01 fails.
- **Fail in shape** (the r_i are not a common factor): the pipeline is
  wrong somewhere — angle rewriting, post-selection or decoding. Diagnose
  by post-selecting on *all* detectors (a lower bound that needs no
  decoder) and by counting decomposition failures in the DEM. P02 and P03
  do not run until this is resolved and recorded.
- **Underpowered** (a point with fewer than 30 logical errors): its shots
  are increased fourfold, once, recorded under Deviations. This is not a
  pass or a fail.

## Deviations

### 2026-10-26 — result, and the registered diagnosis

- The run completed at the registered budget and seeds: no crashes, no
  re-runs, no underpowered point (fewest errors: 117).
- **Registered criterion: FAIL in shape.** Geometric-mean ratio 0.375
  (window 0.80–1.25); ratios 0.11–1.10 (window 0.5–2.0); not a common
  factor. Computed by `tools/analyze_p01.py`, not by hand.
- **Pattern.** Where injection error dominates — θ ≥ 0.1 rad at d = 5,
  θ = 1.58 rad at d = 3 — the pipeline matches the reference within 10%
  (ratios 1.10, 1.05, 1.00, 0.94). Where the memory floor dominates, it
  sits *below* the reference: ×0.11 at d = 3, ×0.51–0.77 at d = 5.
- **R1 (registered):** post-selecting on all detectors gives 0 failures at
  θ = 1e-4 and ~1.1e-4 at θ = 0.1, for both distances — the decoder-free
  lower bound is respected.
- **R2 (registered):** 0 decomposition failures at d = 3 and d = 5; the
  decoder's model is complete.
- **X1 (exploratory, not registered):** shrinking the post-selection window
  raises the floor but cannot reproduce the reference at both distances.
  At d = 3 even zero post-selected rounds gives 7.9e-4 per distance, still
  2.5× below the reference's 2.0e-3; at d = 5 the reference lies between
  the one- and two-round windows. Rejected as an explanation.
- Independent seeds in `p01_diagnosis.json` reproduce the P01 floors
  within their intervals.
- **Cause unresolved.** As registered, P02 and P03 do not run yet.

### 2026-10-26 — two diagnostics added, registered here before they run

- **R3:** decode the same kind of samples with QuEra's own decoder stack —
  `bloqade.decoders.BpLsdDecoder` on tsim's undecomposed detector error
  model. If the reference floor was produced that way, R3 should land on
  it at small θ.
- **R4:** at θ = 1e-4 the circuit is Clifford up to a negligible rotation;
  sample its Clifford proxy with stim instead of tsim and decode
  identically. Agreement checks tsim's sampling of the floor against an
  independent sampler.
- **Gate rule, fixed now, if the cause is still unknown at the end of
  Tue 2026-10-27:** the P01 gate narrows to the injection-dominated regime
  (θ ≥ 0.1 rad), where the pipeline already agrees with the reference
  within 10% — the regime in which α is defined and measured. The floor
  discrepancy is carried into Chapter 10 as an open threat to validity and
  put to QuEra as a direct question. The narrowing is recorded here, today,
  before R3 and R4 exist, so it cannot become "whatever made the result
  look right".

### 2026-10-26 — renumbering only

A four-chapter crash course (Part II) was inserted ahead of the STAR
chapters. P01's chapter is now 10 (was 6), and the threats-to-validity
chapter named in the entry above is now 14 (was 10). Nothing about the
method, the criteria, the budget or the gate changed.

### 2026-10-27 — budgets for R3 and R4, a yardstick R5, and how each reads

Fixed before any of them runs.

- **Samples.** One fresh tsim sample per point, seed `20261028 + d` (and
  `+ 100` for θ = 0.1): d = 3 with 10⁶ shots and d = 5 with 2·10⁶ shots,
  at θ = 10⁻⁴ and θ = 0.1 rad. Post-selection exactly as registered.
- **R3, paired.** Every accepted shot is decoded twice: by matching on the
  Clifford proxy (the registered decoder) and by
  `bloqade.decoders.BpLsdDecoder` with default arguments on tsim's own
  undecomposed detector error model. Decoding is split across 32 worker
  processes; the split does not change any result.
- **R4.** At θ = 10⁻⁴ only, the Clifford proxy (`circuit.stim_circuit`) is
  sampled by stim with the same seed and shot count and decoded by
  matching. Agreement with tsim's matching floor (overlapping 95%
  intervals) validates tsim's sampling of the floor.
- **R5 (reported, not a criterion).** stim's standard rotated-surface-code
  X-memory circuit, distance d, d rounds, uniform circuit noise
  p = 10⁻³ on every channel, matched decoding, 10⁶ shots: an independent
  textbook scale for a d-round memory floor at this p. It is a different
  circuit, so only its order of magnitude is read.
- **How the results read.**
  - If BP-LSD's floor at d = 3, θ = 10⁻⁴ lies within [0.5, 2] of the
    reference *and* its d = 5 floor does too, the discrepancy is
    attributed to the decoder: the reference is consistent with BP-LSD
    decoding, P01 is reported as **reproduced under the reference's
    decoder**, and this book keeps matching (the stronger decoder here) for
    every later protocol, saying so.
  - Otherwise the cause stays unexplained, and the gate rule of
    2026-10-26 applies as written.
  - If R4 disagrees with tsim, every tsim floor in this book is suspect,
    and that is investigated before anything else.
