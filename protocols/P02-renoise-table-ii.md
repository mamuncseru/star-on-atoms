# Protocol P02: re-noise STAR with QuEra's Table II; measure the injection error

- **Status:** COMMITTED
- **Chapter:** 11
- **Registered:** 2026-10-27
- **Artifacts:** p02_validation, p02_injection_error

## The question

Rebuilt on the native gate set under QuEra's own hardware noise model
(Table II of PRX Quantum 7, 020343), scaled to the same combined error
p_ph = 10⁻³ as the published uniform model, what is the injection error of
the published STAR circuits at d = 3 and d = 5 as a function of the logical
angle, and does it follow the one-parameter branch-flip shape
A · f_d(θ) (`starlab.branch_flip_shape`)?

The shape matters for what comes next. If it holds, a noise channel can
change only the constant A, never the angle dependence, and Protocol P03
can measure an error budget at a single angle.

## Circuits and noise

- **Circuits:** `star_d=3.stim` and `star_d=5.stim` as in P01 (commit
  `393312b5de`, SHA-256 checked), angle set by `starlab.with_angle`.
  Logical angles θ_n = π/2ⁿ, n = 2 … 7.
- **Rebuild:** `starlab.renoise.renoise` as committed with this protocol.
  Native gates {R, RX, H, CZ, R_Z, M, MX} plus the published
  `CX[FEED_FORWARD]`; every `CX c t` becomes `H t · CZ c t · H t`. The
  module docstring is the placement table.
- **Window:** noise only in the injection window (`window="injection"`):
  preparation, the pre-rotation rounds, the rotation and the two
  post-rotation rounds, through the last post-selected detector. Later
  rounds are noiseless. This is the registered consequence of P01-R7.
- **Models:**
  - **U** = `uniform(1e-3)`: the published model through the same
    machinery. By check V1 it places exactly the published noise.
  - **T** = `table_ii(p_ph=1e-3)`: every Table II rate times
    s = 10⁻³ / 7.46×10⁻³ = 0.134. Defaults: `hadamards="minimal"`,
    `mover="ancilla"`, CZ loss on spectators, noiseless feed-forward.
- **Variants of T**, one change each, at θ = π/16 only:
  - **T-naiveH:** `hadamards="naive"`.
  - **T-datamove:** `mover="data"`.
  - **T-pairloss:** `loss_on_spectators=False`.
  - **T-ffnoise:** `feedforward_noise=True`.

### Table II, pinned from the PDF (arXiv:2509.18294v2, p. 26)

| Operation | Channel | Rate (s = 1) |
|---|---|---|
| initialization | depolarizing | p_init = 3×10⁻³ |
| 1q gate | depolarizing | 3×10⁻³ |
| atom move | Pauli [p_X, p_Y, p_Z] | [4×10⁻⁵, 4×10⁻⁵, 2×10⁻⁴] |
| atom move loss | Y | 2×10⁻⁵ |
| CZ gate | 2q Pauli | IX = XI = IY = YI = 5×10⁻⁴; IZ = ZI = 6.3×10⁻⁴; ZZ = 1.3×10⁻³; others 0 |
| CZ spectator | Pauli [p_X, p_Y, p_Z] | [5×10⁻⁴, 5×10⁻⁴, 1.3×10⁻³] |
| CZ loss | Y | 1.3×10⁻³ |
| measurement | bit flip | 4×10⁻³ |

Eq. D1, p_ph = p_CZ + 2 p_CZ,loss + p_move + p_move,loss, gives
4.56×10⁻³ + 2.6×10⁻³ + 2.8×10⁻⁴ + 2×10⁻⁵ = 7.46×10⁻³. The paper quotes
"≈ 7.3×10⁻³".

### Readings of the paper's ambiguities (registered now, B5)

1. **1q gate.** Table II says depolarizing 3×10⁻³. App. D b's prose says
   "a biased Pauli channel, reflecting the Z-bias" but gives no numbers.
   This protocol follows the table. It cannot be swept: there is no
   number to sweep to. Listed as a threat.
2. **Initialization.** Depolarizing at 1.5 p_init, after a perfect reset
   (App. D a).
3. **CZ loss.** A Y error "on all qubits in the entangling zone"
   (App. D c (iii)). The default applies it to pair atoms and spectators;
   T-pairloss applies it to pair atoms only.
4. **Transport.** "One qubit from each target pair must first be
   transported", and D1 counts p_move once, so: one move per CZ pair,
   before the CZ. The default moves the ancilla; T-datamove moves the data
   atom. There is no move noise on the way back, and no sitter channel:
   Table II lists none.
5. **Hadamards.** `minimal` cancels H·H and folds an H next to a reset or
   measurement into it (R·H → RX, H·M → MX), as the paper's Fig. 12 draws
   syndrome extraction. `naive` keeps every H with 1q noise (T-naiveH).
   Hadamard counts are reported (V3).
6. **Feed-forward.** The published classically controlled X before the
   rotation is a Pauli-frame update: it can be folded into the sign of the
   next R_Z, so it is noiseless by default. T-ffnoise charges it a 1q gate.
7. **Idle.** Table II has no idle channel. Atoms not acted on during a 1q
   layer, a reset or a measurement see no noise, as in the published
   model.
8. **Measurement.** A bit flip before the measurement: X_ERROR before M,
   Z_ERROR before MX.
9. **Spectators.** Every atom not in a CZ pair during a CZ layer
   (one-zone). App. D c calls the spectator channel "a solid bound".

## Method

- **Sampler.** `starlab.sampling.sample_injection`: tsim
  `compile_detector_sampler(seed)`, drawn in batches of 100,000.
- **Logical error.** Accept a shot iff every detector is zero. A logical
  error is an observable of 1 among accepted shots. There is no decoder.
- **Chunks.** Points run in chunks of 1,000,000 shots (d = 3) or 2,000,000
  (d = 5). A point's estimate pools chunks 0 … m, where m is the first chunk
  at which the cumulative errors reach 400, or the last chunk below the
  cap. Chunks the parallel scheduler computed beyond m are discarded, so
  the estimate does not depend on scheduling.
- **Runner and analysis.** `tools/measure_p02.py` and
  `tools/analyze_p02.py`, as committed with this protocol.

## Checks (deterministic, run first; P02 stops if V1 or V2 fails)

- **V1.** `uniform(1e-3)` through `renoise` reproduces the published
  detector error model: every symptom's probability within 10⁻¹⁵, at
  d = 3, 5 and 7, for all four compile variants (hadamards × mover). As a
  negative control, removing any one role moves some symptom by > 10⁻⁴.
- **V2.** The test suite passes (`tests/test_starlab.py`). This includes:
  - noiseless rebuilt circuits, in both Hadamard modes at d = 3 and 5,
    accept at the ideal rate (5σ) and never fail;
  - one certain Z on a rotated qubit gives the derived survival and flip
    probabilities (5σ).
- **V3.** Accounting: Eq. D1 on Table II = 7.46×10⁻³; the operating point
  = 10⁻³; Hadamard counts per model and window (reported).

**Disclosures.**
- V1 and V2 were run while `renoise.py` was being developed, before this
  protocol was committed. They are properties of the code, not
  measurements.
- A timing smoke test (100,000 shots of U, T and T-naiveH at θ = π/8,
  d = 3 and 5) recorded time and acceptance only; no error counts were
  computed.
- The branch-flip shape was compared with P01-R7's injection-window points
  before registration. R7 used different post-selection (the first
  3(d² − 1) detectors, plus a decoder). There, rate ÷ f had a spread of
  1.19 at d = 3 (3 points) and 1.29 at d = 5 (3 points, one with 40
  errors).

## Budget

- **Points.**
  - Grid: U and T × d ∈ {3, 5} × n = 2 … 7, 24 points.
  - Variants: 4 × 2 distances at n = 4, 8 points. Their baseline is T's
    grid point at n = 4.
- **Stop per point** at 400 errors (about ±10% at 95%) or the cap:
  4×10⁷ shots at d = 3, 10⁸ at d = 5.
- **Seeds.** seed = 10⁶·d + 10⁴·m + 100·n + c, where:
  - m is the model index (U 0, T 1, T-naiveH 2, T-datamove 3,
    T-pairloss 4, T-ffnoise 5);
  - c is the chunk.
- **Parallelism.** At most 10 worker processes, pinned to cores 0–31.
- **Ceiling.** 2.5 hours of wall time (about 12 CPU-hours). A point not
  finished inside it is reported with what it has, flagged `ceiling`.

## Metrics and acceptance criteria

- **Primary metric:** the injection error r = errors / accepted shots,
  with a 95% Wilson interval.
- **H2 (the shape),** per (d, model) for U and T:
  - The test: over the points with ≥ 100 errors (at least 4 of the 6),
    the ratios r_n / f_d(θ_n) have max/min ≤ 1.5.
  - **CONFIRMED** if all four (d, model) pairs pass.
  - **REFUTED** if any pair with ≥ 4 usable points fails.
  - **UNDERPOWERED** otherwise.
- **The constant** A = Σ errors / Σ (accepted × f) over the usable
  points, reported as A / p_ph.
- **Reported with registered expectations** (not pass/fail):
  - **E1:** A_T / A_U at each d. Expected within [0.5, 2]. The reasoning:
    only faults that leave a pure-Z error on the data survive
    post-selection; Table II at the same p_ph is heavier than U on the
    CZ's Z terms and lighter on idles, 1q gates and initialization.
  - **E2:** each variant's injection error over T's at θ = π/16 (Katz
    95% interval), with the acceptance ratio. Expectations:
    - T-naiveH raises the error (more noisy 1q gates on data).
    - T-datamove changes it by < 10%.
    - T-pairloss changes it by < 10% but raises acceptance (loss is a Y
      error, which post-selection removes).
    - T-ffnoise: no expectation registered.
  - **E3:** acceptance at every point, against the ideal.

## Stopping rule

As in the budget: each point stops at 400 errors or the cap. The run ends
when every point has stopped, or at the ceiling.

## What each outcome means

- **V1 or V2 fails:** the re-noiser is not trusted. No measurement runs;
  the code is fixed and P02 is re-registered.
- **H2 CONFIRMED:**
  - The injection error of these circuits is one constant times a known
    function of θ. A noise channel changes only the constant, so P03 can
    measure channel shares at one angle (π/16), and the budget it reports
    holds at every angle.
  - At small θ, these circuits' injection error scales as θ^(2 − 2/d),
    not as the αpθ the paper derives for a teleported rotation with its
    own k = 3 protocol. Chapter 9 must connect the two, not equate them.
- **H2 REFUTED:**
  - A mechanism with a different angle dependence contributes. P03 must
    run its budget at two angles (π/8 and π/64).
  - Chapter 11 says which (d, model) failed and where.
- **UNDERPOWERED:** this is not a null result. A new protocol with a larger
  cap follows.

## Deviations

**2026-10-27, after registration, while the run was in progress and before
any of its results were read: attribution, no change of method.**

The mechanism behind H2 is the paper's, not this book's. Sec. III C 3 of
arXiv:2509.18294v2 (pp. 10–11) writes the injection infidelity as Eq. 2:

  1 − F ≈ P_θ* ε_Z,t + Σ_j P_θ*,j [(1 − ε_tot,j) sin²(Δ_j) + ε_Z,j cos²(Δ_j)],

where:
- j runs over the wrong angles that post-selection can let through;
- Δ_j = (θ − θ_j)/2 is the misrotation;
- the second term "scaling as O(p_ph θ^(2(1 − 1/k))), is the main term
  contributing to infidelity and it stems from the coherent misrotation
  error … the physical Z error interferes with the wrong-angle
  postselection".

`starlab.branch_flip_shape` is that wrong-angle term evaluated in closed
form for the one-Z-fault wrong angle of the k = d teaching circuits:
- the survival factor gives P_θ*,j up to the fault rate;
- sin²(atan t^(k − 2) + atan t^k) gives sin²(Δ_j);
- its small-angle power, θ^(2 − 2/k), is the paper's θ^(2(1 − 1/k)).

The book's contribution is therefore narrower than the protocol's wording
suggests:
- the exact shape at every angle, not only its leading power;
- the fault-injection test that checks both factors on the published
  circuits;
- the measurement of whether one constant fits both models.

Chapter 11 states this attribution. H2, its criterion and its budget are
unchanged. The protocol's sentence contrasting θ^(2 − 2/d) with "the αpθ
the paper derives" stands: the paper's αpθ law is for the teleported
rotation's trace-distance error, and the paper itself contrasts the two.
