# Protocol P01: reproduce QuEra's uniform-noise STAR curve

- **Status:** REPORTED
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

### 2026-10-27 — R3, R4, R5 results; a correction; verdict; a decision

Results (`data/results/p01_diagnosis_r3_r5.json`; rates per distance):

| | d = 3, θ = 1e-4 | d = 5, θ = 1e-4 |
|---|---|---|
| reference | 2.00e-3 | 2.53e-5 |
| matching on tsim samples (R3) | 2.31e-4 | 1.85e-5 |
| BP-LSD on the same samples (R3) | 5.44e-4 | 9.33e-5 |
| matching on stim samples (R4) | 2.30e-4 | 1.54e-5 |
| textbook stim memory, p = 1e-3 (R5) | 2.91e-4 | 3.64e-5 |

- **R3:** BP-LSD is worse than matching here (×2.4 at d = 3, ×5 at
  d = 5) but does not land on the reference (ratios 0.27 and 3.69). By the
  rule fixed this morning, the decoder does not explain the discrepancy.
- **R4:** stim and tsim agree within their intervals at both distances
  (the lower stim acceptance at d = 5 is the expected factor: the proxy
  has no rotation, so its ideal acceptance is 1, not 0.91). tsim's sampling
  of the floor is validated.
- **R5:** the textbook memory floor sits on this book's scale at d = 3
  (×1.3) and is ~7× below the reference; at d = 5 all three agree to
  within ×2.
- **Correction.** The 2026-10-26 gate rule says the pipeline "already
  agrees with the reference within 10%" for θ ≥ 0.1 rad. That is true at
  d = 5 (ratios 1.10, 1.05, 1.00) but **false at d = 3** (0.14, 0.53,
  0.94): the reference's d = 3 floor is so high that it still dominates at
  θ = 0.1 and 0.4. Applied literally, the narrowed gate also fails.

**Verdict (registered criterion): REFUTED.** This pipeline does not
reproduce QuEra's published d = 3 curve. The disagreement is confined to
the memory floor, and on that floor this pipeline agrees with an
independent sampler (R4) and with a textbook memory circuit (R5), while the
reference does not. The cause is unexplained; it is put to QuEra directly.

**Decision, made after seeing R3–R5 and labelled as such.** P02 and P03
proceed on this pipeline. Reasons: (1) every internal check passes — the
noiseless closed form (Ch 6), R1, R2, R4; (2) where the reference is not
dominated by its own floor (d = 5, θ ≥ 0.1) the pipeline matches it within
10%; (3) P02 and P03 measure *changes relative to this pipeline* as one
channel moves, which a fixed offset in an external reference curve cannot
bias. The cost is real and is carried forward: no claim in this book may
say its STAR numbers "reproduce QuEra's", only that they reproduce the
injection regime at d = 5, and Chapter 14 lists the unexplained d = 3
floor as an open threat.

### 2026-10-27 — R6 registered: the "naive pipeline" hypothesis

Proposed by a simulated advisor; two of its factual premises were checked
before registering, without computing any logical error rate:

- tsim's `Circuit.detector_error_model()` defaults to an *undecomposed*
  model, and `pymatching.Matching.from_detector_error_model` accepts it
  without complaint while building its graph only from mechanisms that
  flip at most two detectors. At θ = 1e-4: d = 3 has 706 mechanisms, 421
  of them flipping more than two detectors (19% of the probability; the
  graph keeps 285 edges); d = 5 has 3401, of which 2341 (28%).
- A public ETH QHack 2026 submission (QuEraComputing/ETH_QHACK_2026
  PR #6, `Star2/main2.ipynb`, cell 3, head 778886d697) decodes the d = 3
  circuit exactly this way, post-selecting the first 24 detectors, and
  prints acceptance 0.818 and a logical error rate of 6.92e-3 at
  θ ≈ 3e-4 rad — 2.3e-3 per distance, against the reference's 2.0e-3.

**Hypothesis.** The reference was decoded with matching on tsim's default
(undecomposed) DEM, which drops the multi-detector faults and weakens the
decoder, mostly at d = 3.

**R6.** The registered P01 grid (d = 3, 5; the same eight angles), fresh
samples with seed `20261029 + 1000·d + i`, 10⁶ shots at d = 3 and 2·10⁶ at
d = 5, post-selection as registered. Each accepted shot decoded twice:
matching on the Clifford proxy (this book's decoder) and matching on
tsim's default DEM (the naive pipeline).

**Reading, fixed now.** P01's own registered primary criterion, applied
unchanged to the naive pipeline's sixteen points. If it passes, P01 is
re-reported as *reproduced under the reference's decoder*; the ledger keeps
the REFUTED row and adds a SUPERSEDED pointer; this book keeps the proxy
decoder for everything after, and says why. If it fails, the cause stays
unexplained and nothing else changes.

### 2026-10-27 — R6 result: the reference is reproduced by the naive pipeline

`data/results/p01_r6_naive_pipeline.json`. Under P01's own registered
criterion, the naive pipeline (matching on tsim's default, undecomposed
DEM) **passes**: geometric-mean ratio **1.096** (window 0.80–1.25), ratios
**0.91–1.45** (window 0.5–2.0), over the same sixteen points. On the same
samples this book's proxy decoder reproduces its own P01 numbers (d = 3
floor 2.3e-4 per distance, against the naive pipeline's 2.1e-3).

As fixed before the run: P01 is re-reported as **reproduced under the
reference's decoder**. The reference's d = 3 floor is what matching gives
when PyMatching silently drops the 19% (d = 3) to 28% (d = 5) of fault
probability that flips more than two detectors; decoding the decomposed
Clifford-proxy DEM instead lowers that floor about ninefold at d = 3 and
about twofold at d = 5. This book keeps the proxy decoder for every later
protocol: it is the stronger decoder, and it agrees with an independent
sampler (R4) and a textbook memory circuit (R5).

What this does **not** establish: that QuEra made `star_sim.svg` this way.
It establishes that this pipeline reproduces the plot within the
registered tolerance and that the plot's floor is consistent with it. The
question to QuEra still stands, now with a specific candidate answer.

### 2026-10-27 — R7 registered: is the angle-dependent regime a read-out artifact?

Proposed by a simulated advisor; the mechanism was checked by hand before
registering. After the noisy memory rounds the circuit applies a perfect
inverse rotation exp(+iθ Z₀Z₃Z₆/2) (for d = 3) and reads out logical X.
The decoder only tracks that X observable. A residual physical X error on
a column qubit anticommutes with the rotation's Z-string, so the inverse
rotation adds to the injected one instead of cancelling it, and the
read-out flips with probability sin²θ. If that dominates, P01's
"injection regime" measures uncorrected memory X errors, not injection.

**R7.** Three noise windows on the published circuits, via
`starlab.circuits.restrict_noise`: *all* (P01's circuit), *memory* (noise
only after the last post-selected detector, up to TICK[DISABLE_ERROR]),
*injection* (noise only up to and including the last post-selected
detector). Same post-selection and proxy decoder as P01. θ ∈ {1e-4, 0.1,
0.398, π/4} rad; d = 3 at 10⁶ shots, d = 5 at 2·10⁶; seed
`20261030 + 1000·d + 10·v + i` (v = 0, 1, 2 for all, memory, injection).
Excess(θ) = rate(θ) − rate(1e-4), per accepted shot, per window.

**Reading, fixed now.** The artifact is CONFIRMED at a distance if both:
(i) the memory window's excess ÷ sin²θ at θ = 0.1, 0.398 and π/4 has
max/min ≤ 1.5; and (ii) the memory window's excess is at least half the
all-noise excess at θ = 0.398 and at θ = π/4. Additivity (excess_all ≈
excess_memory + excess_injection within 20%) is reported, not a criterion.

**Consequence, fixed now.** If confirmed at both distances, P02 and P03
measure the injection error with noise in the injection window only and
post-selection on every detector (decoder-free and floor-free), and Ch 10's
"agreement in the injection regime" is restated as agreement in a regime
dominated by the read-out artifact. If not confirmed, P02 keeps P01's
metric and says why.
