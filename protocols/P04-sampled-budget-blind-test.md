# Protocol P04: the error budget, sampled as a blind test of the exact calculation

- **Status:** REPORTED
- **Chapter:** 12
- **Registered:** 2026-10-27
- **Artifacts:** p04_sampled_budget, p04_r1_cz_terms

## The question

P03 CONFIRMED that `starlab.enumerate` reproduces P02. Does its
**per-channel** error budget also hold when sampled? It is computed and
committed below before any of these arms is sampled. The arms are:
- each Table II row switched on alone;
- the top row halved;
- a second angle;
- a distance (d = 7) that no protocol has sampled.

## Circuits and noise

- **Base.** The published circuits, rebuilt by `starlab.renoise`. Default
  readings as in P02: minimal Hadamards, ancilla moves, CZ loss on
  spectators, noiseless feed-forward. Noise only in the injection window;
  every detector post-selected; no decoder.
- **Arms** (`tools/measure_p04.arms()`). All at θ = π/16 and Table II
  scaled to p_ph = 10⁻³, unless stated:
  - **main** arms, sampled to 400 errors:
    - the rows `1q gate`, `CZ spectator` and `CZ gate`, each alone, at
      d = 3 and 5;
    - `d3 1q gate pi/64`: the `1q gate` row alone at d = 3 and θ = π/64;
    - `d7 all-on`: all of Table II at d = 7;
    - `d5 1q gate x0.5`: all of Table II with the `1q gate` row at half
      rate, sampled to 1,000 errors.
  - **small:** `atom move` alone, capped at 4×10⁷ shots. The prediction is
    about 1×10⁻⁶, too rare to reach 400 errors, so it is a count test.
  - **zero:** `initialization`, `measurement`, `CZ loss` and
    `atom move loss`, each alone, capped at 2×10⁷ shots. The prediction is
    exactly 0 at first order.
  - **report:** all of Table II at full strength (s = 1,
    p_ph = 7.46×10⁻³), 2×10⁶ shots at d = 3 and 4×10⁶ at d = 5.
    Acceptance and rate at today's hardware rates.

## Registered predictions

These are the calculator's first-order injection errors, committed in
`data/predictions/p04_exact.json` (from `tools/measure_p04.py --predict`,
calculator at `5b6cd6a`):

| Arm | Predicted | Arm | Predicted |
|---|---|---|---|
| d3 1q gate | 9.681×10⁻⁵ | d5 1q gate | 1.067×10⁻⁴ |
| d3 CZ spectator | 6.866×10⁻⁵ | d5 CZ spectator | 5.713×10⁻⁵ |
| d3 CZ gate | 5.853×10⁻⁵ | d5 CZ gate | 5.512×10⁻⁵ |
| d3 atom move | 1.056×10⁻⁶ | d5 atom move | 1.005×10⁻⁶ |
| d3 zero rows (×4) | 0 | d5 zero rows (×4) | 0 |
| d3 s=1 all-on | 1.666×10⁻³ | d5 s=1 all-on | 1.630×10⁻³ |
| d3 1q gate π/64 | 1.235×10⁻⁵ | d5 1q gate ×0.5 | 1.665×10⁻⁴ |
| d7 all-on | 2.527×10⁻⁴ | | |

Implied shares of the all-on rate at π/16:
- **d = 3:** 1q gate 43%, CZ spectator 31%, CZ gate 26%, atom move 0.5%,
  everything else 0.
- **d = 5:** 1q gate 48%, CZ spectator 26%, CZ gate 25%, atom move 0.5%,
  everything else 0.

## Method

- **Sampling.** `starlab.sampling.sample_injection`, in chunks of 10⁶
  (d = 3) or 2×10⁶ (d = 5, 7) shots, through `tools/chunked.run`. That is
  P02's scheduler, generalised; P02's own runner is unchanged.
- **Stopping.** An arm stops at its error target or its cap.
- **Seeds.** Seed = 10⁷ + 10⁵·(arm index) + chunk.
- **Load.** 10 workers, run as `nice -n 19 taskset -c 0-31`.
- **Smoke test, disclosed.** A one-off d = 7 timing test (10⁵ shots,
  time and acceptance only: 5.4k shots/s, acceptance 0.020) was run
  before registration. It computed no error count.

## Budget

- **Caps:** as listed under the arms. About 1 hour of wall time,
  dominated by `d7 all-on` (about 8×10⁷ shots).
- **Ceiling:** 2.5 h of wall time.

## Metrics and acceptance criteria

Each arm gets a 95% Wilson interval [lo, hi]. C is the arm's predicted
rate.

- **Main arm:** *consistent* if lo × 0.92 ≤ C ≤ hi × 1.08 (the P03 model
  tolerance on top of statistics); *inconsistent* if C < lo × 0.85 or
  C > hi × 1.18.
- **Zero row:** *consistent* if its 95% upper bound is below 1% of P02's
  all-on rate at the same d (2.25×10⁻⁴ at d = 3, 2.31×10⁻⁴ at d = 5);
  *inconsistent* if its lower bound is above 1%.
- **Small row:** *consistent* if the observed count lies in the two-sided
  99% Poisson interval of C × accepted.
- **CONFIRMED** if every main, zero and small arm is consistent.
  **REFUTED** if any is inconsistent. **INCONCLUSIVE** otherwise.
- **Reported:**
  - **Sampled additivity:** Σ single-on rates at π/16 ÷ P02's all-on rate,
    per d.
  - **Acceptance per arm.** Registered expectation: every single-on arm
    accepts more often than P02's all-on, and the zero rows' acceptance
    falls below the noiseless ideal. They cost shots, not fidelity.
  - **The s = 1 rows against C.** First order is expected to degrade at
    p_ph = 7.46×10⁻³. Not scored.

## Stopping rule

Each arm stops at its target or cap. The run ends when all have stopped,
or at the ceiling.

## What each outcome means

- **CONFIRMED:** the per-channel budget is measured as well as computed.
  - The headline: what halving each channel buys, which is exact at first
    order and sampled for the top row.
  - Chapter 12 then reports the calculator's budget at d = 3–15 and its
    per-CZ-Pauli-term sensitivities as computed results, validated at
    d = 3, 5 and 7.
- **REFUTED:**
  - The budget is reported as sampled, and the calculator is limited to
    the circuits where it was validated (P02's).
  - The failing arms identify the missing mechanism.
- **INCONCLUSIVE:** the budget is reported with both numbers side by side,
  and no exact claim is made for the inconclusive rows.

## Deviations

**2026-10-27, while P04 was running and before any of its results were
read: diagnostic R1 registered (the CZ channel by parameter).**

- **The finding to test.** Computed by the calculator after P03, while
  writing Chapter 12:
  - Table II's CZ channel has three parameters: a single X or Y on either
    atom (5×10⁻⁴ each term), a single Z (6.3×10⁻⁴), and the correlated ZZ
    (1.3×10⁻³, its largest).
  - The calculator says ZZ adds **exactly nothing** to the injection
    error, and the X/Y terms add more than the Z terms.
  - The stated reason: the ancilla half of ZZ always flips that ancilla's
    measurement, and the data qubits sit in the Hadamard frame during
    X-check CZs.
- **Arms** (`tools/measure_p04_r1.py`). The CZ channel alone, at Table II
  rates × 0.134, restricted to one parameter group, at π/16, d = 3 and 5:
  - **ZZ only:** a P04 "zero" arm, capped at 2×10⁷ shots;
  - **single Z only** and **single X/Y only:** P04 "main" arms, to 400
    errors.
- **Predictions**, committed in `data/predictions/p04_r1_exact.json`:

  | Arm | d = 3 | d = 5 |
  |---|---|---|
  | ZZ only | 0 | 0 |
  | single Z only | 2.773×10⁻⁵ | 2.373×10⁻⁵ |
  | single X/Y only | 3.081×10⁻⁵ | 3.139×10⁻⁵ |

  The two non-zero arms sum to the CZ row of P04's table.
- **Scoring.** P04's own (`measure_p04.score`), with P04's verdict rule
  applied to these six arms.
- **Seeds and order.** Seed = 2×10⁷ + 10⁵·arm + chunk. Run after P04
  finishes, so the two never share the 32 cores.
- **Artifact:** `data/results/p04_r1_cz_terms.json`.

**2026-10-28: first launch interrupted; rerun identically.**
- **What happened.** The first launch (2026-10-27, 22:15) was killed at
  1,365 s, when the agent session that started it ended. 20 of the 21
  arms had stopped; `d7 all-on` had not.
- **What was lost and seen.** Per-chunk counts lived only in the
  runner's memory. No artifact was written, and no rate or error count
  was read: the log holds only stop lines.
- **The rerun.** Same code, seeds, chunks and stopping rules, so the 20
  finished arms reproduce exactly. R1 follows it as registered. Both run
  detached from the session (`setsid nohup`), still under
  `nice -n 19 taskset -c 0-31`.

**2026-10-28, after the rerun: the result.** No deviation from method.
- **The run.** 552 million shots in 4,712 s of wall time (ceiling 2.5 h).
  All nine main arms stopped at their error targets; the other twelve at
  their caps, as registered. `d7 all-on` took 7.8×10⁷ shots.
- **CONFIRMED.** Every main, zero and small arm is consistent.

  | Arm | Errors | Measured | Predicted | Measured ÷ predicted |
  |---|---|---|---|---|
  | d3 1q gate | 416 | 9.41×10⁻⁵ | 9.68×10⁻⁵ | 0.97 |
  | d3 CZ spectator | 416 | 7.54×10⁻⁵ | 6.87×10⁻⁵ | 1.10 |
  | d3 CZ gate | 425 | 6.08×10⁻⁵ | 5.85×10⁻⁵ | 1.04 |
  | d5 1q gate | 409 | 1.15×10⁻⁴ | 1.07×10⁻⁴ | 1.07 |
  | d5 CZ spectator | 410 | 5.65×10⁻⁵ | 5.71×10⁻⁵ | 0.99 |
  | d5 CZ gate | 406 | 5.23×10⁻⁵ | 5.51×10⁻⁵ | 0.95 |
  | d5 1q gate ×0.5 | 1,010 | 1.70×10⁻⁴ | 1.67×10⁻⁴ | 1.02 |
  | d3 1q gate π/64 | 402 | 1.35×10⁻⁵ | 1.24×10⁻⁵ | 1.09 |
  | d7 all-on | 404 | 2.60×10⁻⁴ | 2.53×10⁻⁴ | 1.03 |

  - **Small rows.** `atom move`: 31 errors at d = 3 (99% Poisson
    interval of the prediction [12, 37]); 6 at d = 5 ([2, 16]).
  - **Zero rows.** Not zero, but far below the 1% limit: 11 errors in
    4.4×10⁷ accepted shots over the four d = 3 rows, 2 in 1.4×10⁷ at
    d = 5. The largest 95% upper bound is 0.67% of the all-on rate
    (`d5 measurement`).
- **Reported.**
  - **Sampled additivity:** 1.04 (d = 3), 0.97 (d = 5).
  - **Acceptance.** As registered. Every single-on arm accepts more often
    than P02's all-on (0.538–0.565 against 0.475 at d = 3; 0.162–0.191
    against 0.115 at d = 5), and every zero row accepts less than the
    noiseless ideal. For `atom move loss` the drop is only about 0.01
    percentage points, too small to resolve at 2×10⁷ shots.
  - **s = 1 rows.** Measured ÷ first order = 1.10 [1.01, 1.19] at d = 3
    (566 errors, acceptance 0.155), and 1.19 [0.85, 1.67] at d = 5 (33
    errors, acceptance 0.0043). At d = 3 the excess is resolved: first
    order is already 10% low at today's hardware rates.
  - **Halving, sampled.** P02's all-on ÷ `d5 1q gate x0.5` = 1.36
    [1.21, 1.52] (Katz). The calculator's G^sim = 1/(1 − f/2) = 1.32.
  - **The largest residuals sit where first order is weakest:** the
    smallest angle (π/64, +9%) and full strength (+10%). The exception is
    `d3 CZ spectator` (+10%, the prediction on the edge of its Wilson
    interval), which nothing singles out.

**2026-10-28, after the R1 run: the result.** No deviation from method.
250 million shots in 876 s of wall time.
- **CONFIRMED.**

  | Arm | Errors / accepted | Measured | Predicted |
  |---|---|---|---|
  | d3 CZ ZZ only | 2 / 1.11×10⁷ | 1.8×10⁻⁷ (upper 0.29% of all-on) | 0 |
  | d3 CZ single Z only | 402 / 1.39×10⁷ | 2.89×10⁻⁵ | 2.77×10⁻⁵ |
  | d3 CZ single X/Y only | 402 / 1.27×10⁷ | 3.16×10⁻⁵ | 3.08×10⁻⁵ |
  | d5 CZ ZZ only | 0 / 3.6×10⁶ | 0 (upper 0.46% of all-on) | 0 |
  | d5 CZ single Z only | 400 / 1.71×10⁷ | 2.34×10⁻⁵ | 2.37×10⁻⁵ |
  | d5 CZ single X/Y only | 407 / 1.21×10⁷ | 3.36×10⁻⁵ | 3.14×10⁻⁵ |

- **The mechanism, checked after the run** by planting one fault at a
  time in the d = 3 circuit
  (`test_cz_faults_hide_only_as_the_frame_predicts`):
  - every ancilla is prepared and measured in X, so a Z or Y on the
    ancilla half of any window CZ flips a detector that no branch flips
    (84 of 84 sites at d = 3; 280 of 280 at d = 5). This is why ZZ is
    free;
  - an X on the ancilla half can hide, by spreading through the
    ancilla's later CZs into Zs on data (3 sites at d = 3, 4 at d = 5);
  - on the data half, only an X inside the Hadamard frame (4 sites at
    d = 3, 6 at d = 5) or a Z outside it (5, 6) can hide, and a Y never
    does;
  - the hideable X sites add up to the computed X/Y sensitivity (7 at
    d = 3, 10 at d = 5) and the Z sites to the Z sensitivity (5, 6). R1's
    registered reason named the data qubits' frame only; the ancilla's X
    is the rest.
