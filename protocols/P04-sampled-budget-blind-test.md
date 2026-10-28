# Protocol P04: the error budget, sampled as a blind test of the exact calculation

- **Status:** COMMITTED
- **Chapter:** 12
- **Registered:** 2026-10-27
- **Artifacts:** p04_sampled_budget

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

None yet.
